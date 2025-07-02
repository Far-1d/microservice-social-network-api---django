from rest_framework import serializers
from apps.profiles.models import ProfilePrivacy


class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePrivacy
        fields = [
            'show_email',
            'show_photo',
            'show_bio',
            'show_location',
            'show_social_links',
        ]


class PrivacyUpdateSerializer(PrivacySerializer):
    pass