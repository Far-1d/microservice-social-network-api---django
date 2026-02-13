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
import logging
from apps.communications.events import UserEventManager

logger = logging.getLogger(__name__)

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
        print("V1 is called")
        # check there is no deleted user with the same email
        # if so, delete it (to do : move deleted user to another table)
        try:
            deleted_user = User.objects.get(email=serializer.validated_data.get('email'))
            logger.warning(f"a new user attempts to create account using a deleted account's email")
            logger.warning(f"email:{deleted_user.email},  deleted at: {deleted_user.deleted_at}")
            if deleted_user.deleted:
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
            return Response(
                {'message': _('User not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # generate token
        token_serializer = CustomTokenObtainPairSerializer(context={'user': user})

        tokens = token_serializer.validate({})

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
            logger.info(f'Sending password reset code to {user.email}')
            send_email(
                "password reset request",
                f"your code is {password_reset.code}",
                [user.email]
            )
        else:
            pass

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
                logger.warning(f"Password reset attempt for inactive user: {user.email}")
                return Response(
                    {'message':_('User not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            user.set_password(serializer.validated_data['password'])
            user.save(update_fields=['password'])
            password_reset.delete()

            logger.info(f"Password reset successful for user: {user.email}")

            return Response(
                {'message': _('Password reset successful')},
                status=status.HTTP_200_OK
            )
        
        except PasswordResetCode.DoesNotExist:
            logger.warning(f"Invalid password reset code attempt: {serializer.validated_data.get('code')}")
            return Response(
                {'message': _('Failed to verify code, please try again in a few moments.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except PasswordResetCode.MultipleObjectsReturned:
            logger.critical(f"Multiple password reset codes found for code: {serializer.validated_data.get('code')}")
            PasswordResetCode.objects.filter(code=serializer.validated_data['code']).delete()
            return Response(
                {'message': _('System error. Please request a new code.')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"Password reset error: {str(e)}", exc_info=True)
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
        user = request.user

        if user.deleted:
            return Response(
                {
                    'message': _('User not found'),
                },
                status=status.HTTP_404_NOT_FOUND
            )

        user.soft_delete()
        
        logger.info(f'user {user.username} soft deleted')

        # send user info to other services
        events = UserEventManager()
        events.publish('delete', user)
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )