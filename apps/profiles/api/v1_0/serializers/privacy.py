from rest_framework import serializers
from apps.profiles.models import ProfilePrivacy


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePrivacy
        fields = [
            'show_email',
            'show_photo',
            'show_bio',
        ]


class PrivacyUpdateSerializer(PrivacySerializer):
    pass