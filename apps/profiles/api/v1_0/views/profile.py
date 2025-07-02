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
from apps.profiles.api.v1_0.serializers.profile import (
    ProfileReadSerializer,
    ProfileListSerializer,
    ProfileUpdateSerializer
)


# privacy filters are done in serializer


class ProfileReadApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug:str):
        try:
            profile = Profile.objects.select_related('user', 'privacy').get(user__slug=slug)
        except Profile.DoesNotExist:
            return Response(
                {'message': _('Profile not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProfileReadSerializer(
            profile, 
            context={'request': request}
        )
        serialized_data = serializer.data
        
        return Response(
            serialized_data,
            status=status.HTTP_200_OK
        )

class ProfileListApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = Profile.objects.exclude(user=request.user)

        # seach filtering
        if q:= request.GET.get('q'):
            profiles = profiles.filter(
                Q(user__username__icontains=q) |
                Q(bio__icontains=q)
            )

        # Pagination
        paginator = Paginator(profiles, 20)  # 20 items per page
        page_number = request.GET.get('page', 1)
        
        try:
            page = paginator.page(page_number)
        except EmptyPage:
            raise ValidationError("Invalid page number")
        
        serializer = ProfileListSerializer(
            page.object_list, 
            many=True,
            context={'request': request}
        )

        return Response(
            {
                'results': serializer.data,
                'pagination': {
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'has_next': page.has_next(),
                    'has_previous': page.has_previous(),
                    'count': paginator.count
                }
            },
            status=status.HTTP_200_OK
        )

class ProfileUpdateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        profile = request.user.profile

        serializer = ProfileUpdateSerializer(
            instance=profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        updated_profile = serializer.save()

        response_serializer = ProfileReadSerializer(
            updated_profile,
            context={'request': request}
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

