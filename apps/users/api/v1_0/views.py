from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from apps.base.serializers import CustomTokenObtainPairSerializer
from apps.users.models import (
    User,
    PasswordResetCode,
)
from apps.profiles.models import Profile, ProfilePrivacy
from apps.users.api.v1_0.serializers import (
    UserSignupSerializer,
    UserLoginSerializer,
    UserPasswordForgotSerializer,
    UserPasswordResetSerializer,
    UserUpdateSerializer,
    UserSimpleSerializer
)
from apps.users.utils import generate_random_code
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from django.conf import settings
from django.db import transaction
from apps.users.utils import send_email
from settings.logging import get_logger
from apps.communications.events import UserEventManager
from utils.metrics import (
    new_users_total, 
    login_attempts_total,
    password_reset_requests_total,
    users_deleted_total
)

logger = get_logger('user_v1')

class UserReadApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        serializer = UserSimpleSerializer(
            user,
            context = {'request':request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class UserSignupApi(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # check there is no deleted user with the same email
        # if so, delete it (to do : move deleted user to another table)
        try:
            deleted_user = User.objects.get(email=serializer.validated_data.get('email'))
            if deleted_user.deleted:
                logger.warning(f"Deleted_account_recreation", email=deleted_user.email, deleted_at=str(deleted_user.deleted_at))
                deleted_user.delete()

        except User.DoesNotExist:
            pass

        user = serializer.save()

        profile = Profile.objects.create(
            user=user
        )

        profile_privacy = ProfilePrivacy.objects.create(
            profile=profile
        )

        # generate token
        token_serializer = CustomTokenObtainPairSerializer(
            context={'user': user}
        )

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

class UserLoginApi(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request) -> Response:
        
        # don't allow logged in user to login again
        if request.user.is_authenticated:
            logger.warning(f'Already_logged_in')
            login_attempts_total.labels(status='failed').inc()
            return Response(
                {'message': _('You are already logged in')},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login_identifier = serializer.validated_data.get('login_identifier')
        password = serializer.validated_data.get('password')


        user = authenticate(
            request,
            username=login_identifier,
            password=password
        )

        if not user:
            try:
                user = User.objects.get(email=login_identifier)
                user = authenticate(
                    request,
                    username=user.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        
        if not user or user.deleted:
            login_attempts_total.labels(status='failed').inc()
            return Response(
                {'message': _('User not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # generate token
        token_serializer = CustomTokenObtainPairSerializer(context={'user': user})

        tokens = token_serializer.validate({})

        login_attempts_total.labels(status='success').inc()
        return Response(
            tokens,
            status=status.HTTP_200_OK
        )

class UserPasswordForgotApi(APIView):
    permission_classes = [permissions.AllowAny]
    CODE_EXPIRY_MINUTES = 5

    @transaction.atomic
    def post(self, request) -> Response:
        serializer = UserPasswordForgotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.regular_objects.get(email=serializer.validated_data.get("email"))
        except User.DoesNotExist:
            return Response(
                {'message': _('If this email exists, a reset code has been sent')},
                status=status.HTTP_200_OK  # Don't reveal if user exists
            )

        # delete any existing code
        PasswordResetCode.objects.filter(user=user).delete()
        
        password_reset = PasswordResetCode.objects.create(
            user=user,
            code=generate_random_code()
        )
        
        # send email
        if settings.DEBUG:
            logger.info(f'Password_reset_sending_email', email=user.email)
            send_email(
                "password reset request",
                f"your code is {password_reset.code}",
                [user.email]
            )
        else:
            pass
        
        logger.info(f'Password_forgot_created', user_id=str(user.id))
        
        password_reset_requests_total.inc()

        return Response(
            {
                'message': _('If this email exists, a reset code has been sent'),
                'expiry': (password_reset.created_at + timedelta(minutes=self.CODE_EXPIRY_MINUTES)).strftime("%d/%m/%Y, %H:%M:%S UTC")
            },
            status=status.HTTP_200_OK
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

class UserUpdateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request) -> Response:
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user:User = request.user
        
        if user.deleted:
            logger.warning("Update_deleted_user", deleted_at=str(user.deleted_at))
            return Response(
                {'message':_('User not found')},
                status=status.HTTP_404_NOT_FOUND
            )

        if email := serializer.validated_data.get('email'):
            user.email = email
        if  password := serializer.validated_data.get('password'):
            user.set_password(password)
        
        # notify user that only email or password is updatable
        if 'email' not in serializer.validated_data.keys() and \
           'password' not in serializer.validated_data.keys():
            return Response(
                {'message':_('Only email and password are updatable')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        
        response_serializer = UserSimpleSerializer(
            user,
            context = {'request':request}
        )

        # send user info to other services
        events = UserEventManager()
        events.publish('update', user)

        return Response(
            {
                'message': _('Account update successful'),
                **response_serializer.data
            },
            status=status.HTTP_200_OK
        )

class UserDeleteApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request) -> Response:
        user:User = request.user

        if user.deleted:
            logger.warning("Delete_deleted_user", deleted_at=str(user.deleted_at))
            return Response(
                {
                    'message': _('User not found'),
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user.soft_delete()
        
        logger.info(f'Delete_user_success')

        # send user info to other services
        events = UserEventManager()
        events.publish('delete', user)
        
        users_deleted_total.inc()
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )