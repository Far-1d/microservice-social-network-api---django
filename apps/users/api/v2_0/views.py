from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from apps.profiles.models import Profile, ProfilePrivacy
from apps.users.api.v1_0.serializers import (
    UserSignupSerializer, 
    UserSimpleSerializer,
    UserPasswordResetSerializer
)
from apps.base.serializers import CustomTokenObtainPairSerializer
from apps.users.utils import validate_password
from django.db import transaction
from apps.communications.events import UserEventManager
from apps.users.models import User, PasswordResetCode
from django.utils import timezone
from datetime import timedelta
from settings.logging import get_logger
from utils.metrics import new_users_total

logger = get_logger('user_v2')

class UserSignupApi(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            deleted_user = User.objects.get(email=serializer.validated_data.get('email'))
            if deleted_user.deleted:
                logger.warning(f"Deleted_account_recreation", email=deleted_user.email, deleted_at=str(deleted_user.deleted_at))
                deleted_user.delete()

        except User.DoesNotExist:
            pass
        
        password = request.data.get('password', '')
        valid, errors = validate_password(password)

        if not valid:
            return Response(
                {'message': _('Password not stong enough.'), 'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        profile = Profile.objects.create(
            user=user
        )
        profile_privacy = ProfilePrivacy.objects.create(
            profile=profile
        )

        # generate token
        token_serializer = CustomTokenObtainPairSerializer(context={'user': user})

        tokens = token_serializer.validate({})

        # send user info to other services
        events = UserEventManager()
        events.publish('create', user)

        new_users_total.inc()
        
        return Response(
            {
                'message': _('Account create successful'),
                **tokens
            },
            status=status.HTTP_201_CREATED
        )


class UserPasswordResetApi(APIView):
    permission_classes = [permissions.AllowAny]
    CODE_EXPIRY_MINUTES = 5
    
    @transaction.atomic
    def post(self, request) -> Response:
        serializer = UserPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get code object
        try:
            password_reset = PasswordResetCode.objects.select_related('user').select_for_update().get(
                code=serializer.validated_data['code']
            )

            # Check if Code has expired (e.g., 5 minutes)
            if timezone.now() > password_reset.created_at + timedelta(minutes=self.CODE_EXPIRY_MINUTES):
                password_reset.delete()

                return Response(
                    {'message':_('Code has expired. Please request a new one.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = password_reset.user

            # check user is not deleted
            if user.deleted or not user.is_active:
                logger.warning(f"Inactive_user_password_reset", user_id=str(user.id), email=user.email)
                return Response(
                    {'message':_('User not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # v2.0 change
            password = request.data.get('password', '')
            valid, errors = validate_password(password)

            if not valid:
                return Response(
                    {'message': _('Password not stong enough.'), 'errors': errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # end

            user.set_password(serializer.validated_data['password'])
            user.save(update_fields=['password'])
            password_reset.delete()

            logger.info(f"Password_reset_success", user_id=str(user.id), email=user.email)

            return Response(
                {'message': _('Password reset successful')},
                status=status.HTTP_200_OK
            )
        
        except PasswordResetCode.DoesNotExist:
            return Response(
                {'message': _('Failed to verify code, please try again in a few moments.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except PasswordResetCode.MultipleObjectsReturned:
            logger.critical(f"Multiple_password_reset_codes", code=serializer.validated_data.get('code'))
            PasswordResetCode.objects.filter(code=serializer.validated_data['code']).delete()
            return Response(
                {'message': _('System error. Please request a new code.')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"Password_reset_error", error=str(e), exc_info=True)
            return Response(
                {'message': _('An error occurred during password reset')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

