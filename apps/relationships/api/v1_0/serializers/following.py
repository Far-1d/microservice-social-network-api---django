from rest_framework import serializers
from apps.relationships.models import (
    Following, 
    FollowRequest
)
from apps.users.api.v1_0.serializers import UserSimpleSerializer

class FollowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Following
        fields = [
            'user',
            'following'
        ]

class FollowerRequestListSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer()

    class Meta:
        model = FollowRequest
        fields = ['user', 'message']

class FollowingRequestListSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(source='following')

    class Meta:
        model = FollowRequest
        fields = ['user', 'message']

class FollowRequestSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    message = serializers.CharField(required=False)

class FollowRequestAcceptSerializer(serializers.Serializer):
    slug = serializers.SlugField()
    accept = serializers.BooleanField()

class FollowRequestDeleteSerializer(serializers.Serializer):
    slug = serializers.SlugField()

class FollowToggleSerializer(FollowRequestDeleteSerializer):
    pass