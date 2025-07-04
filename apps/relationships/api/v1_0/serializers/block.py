from rest_framework import serializers
from apps.relationships.models import (
    Block
)
from apps.users.api.v1_0.serializers import UserSimpleSerializer

class BlockSerializer(serializers.Serializer):
    slug = serializers.SlugField()