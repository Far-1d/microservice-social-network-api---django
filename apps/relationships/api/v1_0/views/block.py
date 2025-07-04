from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q
from apps.relationships.models import (
    Block,
    Following
)
from apps.users.models import User
from apps.relationships.api.v1_0.serializers.block import BlockSerializer
from apps.users.api.v1_0.serializers import UserSimpleSerializer

class BlockApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        blocks = [blocks.blocked for blocks in user.blocked_users.all()]

        serializer = UserSimpleSerializer(
            blocks,
            many=True,
            context={'request': request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def post(self, request):
        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            blocked_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # stop self-request
        if request.user == blocked_user:
            return Response (
                {'message': _('You cannot block yourself')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # stop blocked users from sending request
        if Block.objects.filter(user=blocked_user, blocked=request.user).exists():
            return Response(
                {'message': 'You are blocked by this user'},
                status=status.HTTP_403_FORBIDDEN
            )

        # stop duplicate requests
        blocks = Block.objects.filter(
            user=request.user,
            blocked=blocked_user
        )
        if blocks.exists():
            return Response(
                {'message': _('Already Requested')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # remove following relationships
        Following.objects.filter(
            Q(user=request.user,following=blocked_user) |
            Q(user=blocked_user,following=request.user) 
        ).delete()

        Block.objects.create(
            user=request.user,
            blocked=blocked_user
        )

        return Response(
            {'message': _('Block successful')},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            blocked_user = User.regular_objects.get(slug=serializer.validated_data['slug'])
        except User.DoesNotExist:
            return Response(
                {'message': _('Account not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        Block.objects.filter(
            user=request.user, 
            blocked=blocked_user
        ).delete()

        return Response(
            {'message': _('Request remove successful')},
            status=status.HTTP_200_OK
        )
    