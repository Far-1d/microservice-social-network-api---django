from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from apps.relationships.models import (
    Following,
    FollowRequest,
    Block
)
from apps.relationships.api.v1_0.serializers.following import (
    FollowRequestSerializer,
    FollowingRequestListSerializer,
    FollowerRequestListSerializer,
    FollowRequestAcceptSerializer,
    FollowRequestDeleteSerializer,
    FollowToggleSerializer
)
from apps.users.models import User
from apps.users.api.v1_0.serializers import UserSimpleSerializer
import logging

logger = logging.getLogger(__name__)

class FollowCountReadApi(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug) -> Response:
        try:
            user = User.regular_objects.get(slug=slug)
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {
                'followers': user.followers.count(),
                'followings': user.followings.count()
            },
            status=status.HTTP_200_OK
        )


class FollowerReadApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug) -> Response:
        try:
            user = User.regular_objects.get(slug=slug)
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # only following user and staff can view private profiles followers
        is_following = Following.objects.filter(
            user=request.user,
            following=user
        ).exists()

        if user.profile.is_public and not request.user.is_staff and not is_following:
            return Response(
                {'message': _('You cannot view folllowers of private profiles')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        followers = [fr.user for fr in user.followers.all()]

        serializer = UserSimpleSerializer(
            followers,
            many=True,
            context={'request': request} 
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class FollowingReadApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug) -> Response:
        try:
            user = User.regular_objects.get(slug=slug)
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # only following user and staff can view private profiles followings
        is_following = Following.objects.filter(
            user=request.user,
            following=user
        ).exists()

        if user.profile.is_public and not request.user.is_staff and not is_following:
            return Response(
                {'message': _('You cannot view folllowers of private profiles')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        followings = [fr.following for fr in user.followings.all()]

        serializer = UserSimpleSerializer(
            followings,
            many=True,
            context={'request': request} 
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class FollowRequestApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Requests sent TO the current user (people who want to follow them)
        follower_requests = user.follow_requests.all()

        # Requests sent BY the current user (people they want to follow)
        following_requests = user.requests.all()

        follower_serializer = FollowerRequestListSerializer(
            follower_requests,
            many=True,
            context={'request': request}
        )
        
        following_serializer = FollowingRequestListSerializer(
            following_requests,
            many=True,
            context={'request': request}
        )

        return Response(
            {
                'follower_requests': follower_serializer.data,
                'following_requests': following_serializer.data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = FollowRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            followed_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )

        # stop self-request
        if request.user == followed_user:
            return Response (
                {'message': _('You cannot request yourself')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # stop blocked users from sending request
        if Block.objects.filter(user=followed_user, blocked=request.user).exists():
            return Response(
                {'message': 'You are blocked from requesting this user'},
                status=status.HTTP_403_FORBIDDEN
            )

        # stop duplicate requests
        requests = FollowRequest.objects.filter(
            user=request.user,
            following=followed_user
        )
        if requests.exists():
            return Response(
                {'message': _('Already Requested')},
                status=status.HTTP_400_BAD_REQUEST
            )

        FollowRequest.objects.create(
            user=request.user,
            following=followed_user,
            message=serializer.validated_data['message']
        )

        return Response(
            {'message': _('Request successful')},
            status=status.HTTP_200_OK
        )

    def delete(self, request): 
        serializer = FollowRequestDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            followed_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )

        FollowRequest.objects.filter(
            user=request.user,
            following=followed_user
        ).delete()

        return Response(
            {'message': _('Request remove successful')},
            status=status.HTTP_200_OK
        )


class FollowRequestResponseApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FollowRequestAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            requested_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        requests = FollowRequest.objects.filter(
            user=requested_user,
            following=request.user,
        )

        if not requests.exists():
            return Response(
                {'message': _('Request not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        request_accepted = serializer.validated_data['accept']
        if request_accepted:
            Following.objects.create(
                user=requested_user,
                following=request.user
            )
        
        # remove request
        requests.delete()
        
        return Response(
            {'message': _('Request accept successful' if request_accepted else 'Request reject successfull')},
            status=status.HTTP_200_OK
        )


class FollowToggleApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = FollowToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            followed_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # stop self-request
        if request.user == followed_user:
            return Response (
                {'message': _('You cannot follow yourself')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # prevent follow if blocked
        if Block.objects.filter(user=followed_user, blocked=request.user).exists():
            return Response(
                {'message': 'You are blocked from following this user'},
                status=status.HTTP_403_FORBIDDEN
            )

        follow, created = Following.objects.get_or_create(
            user=request.user,
            following=followed_user,
            defaults={}
        )

        if not created:
            follow.delete()
            
            return Response(
                {
                    'message': _('Unfollowed successfully'),
                    'user': followed_user.username,
                    'status': 0     # 0 = not-following
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                'message': _('Now following'),
                'user': followed_user.username,
                'status': 1     # 1 = following
            },
            status=status.HTTP_201_CREATED
        )
