from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage
from django.utils.translation import gettext_lazy as _
from apps.profiles.models import (
    Profile, 
    ProfilePrivacy
)
from apps.users.models import User
from apps.profiles.api.v2_0.serializers.privacy import (
    PrivacySerializer,
    PrivacyUpdateSerializer,
)
import logging

logger = logging.getLogger(__name__)


class PrivacyReadApi(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, slug:str):
        try:
            # Try to find by User slug
            user = User.regular_objects.get(slug=slug)
            profile = user.profile
            privacy = profile.privacy
        
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Profile.DoesNotExist:
            logger.warning(f'no profile for user {user.username} found')

            profile = Profile.objects.create(user=user)
            privacy = ProfilePrivacy.objects.create(profile=profile)

        except ProfilePrivacy.DoesNotExist:
            # Handle case where privacy settings don't exist
            logger.warning(f'no privacy for user {user.username} found. profile : {profile}')
            privacy = ProfilePrivacy.objects.create(profile=profile)

        except Exception as e:
            logger.error(f'privacy read error: {e}', exc_info=True)

        serializer = PrivacySerializer(privacy)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
class PrivacyUpdateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        privacy = request.user.profile.privacy

        serializer = PrivacyUpdateSerializer(
            instance=privacy,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        updated_privacy = serializer.save()

        response_serializer = PrivacySerializer(updated_privacy)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )