from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from apps.profiles.models import Profile, ProfilePrivacy
from apps.users.api.v1_0.serializers import (
    UserSignupSerializer, 
    UserSimpleSerializer
)
from apps.base.serializers import CustomTokenObtainPairSerializer
from apps.users.utils import validate_password
from django.db import transaction


class UserSignupApi(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request) -> Response:
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, errors = validate_password(serializer.validated_data['password'])

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

        return Response(
            {
                'message': _('Account create successful'),
                **tokens
            },
            status=status.HTTP_201_CREATED
        )


