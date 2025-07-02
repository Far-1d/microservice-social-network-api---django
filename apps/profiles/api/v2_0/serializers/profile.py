from rest_framework import serializers
from apps.profiles.models import (
    Profile,
    ProfilePrivacy
)
from apps.relationships.models import Following
from apps.users.api.v1_0.serializers import UserSimpleSerializer
from apps.profiles.utils import apply_privacy_v2

class ProfileListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    username_slug = serializers.CharField(source='user.slug', read_only=True)


    class Meta:
        model = Profile
        fields = [
            'username',
            'username_slug',
            'bio',
            'photo',
            'is_public',
            'location',
        ]
    
    def to_representation(self, instance):
        request = self.context.get('request')
        return apply_privacy_v2(instance, request.user)
    
class ProfileReadSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'user',
            'bio',
            'photo',
            'is_public',
            'location',
            'social_links',
        ]
    
    def to_representation(self, instance):
        request = self.context.get('request')
    
        data = super().to_representation(instance)    

        profile = instance
        if not profile.is_public:
                # filter only if the requesting user is neither the profile owner nor a staff member
                if not request.user.is_staff and profile.user != request.user :
                    
                    # check following
                    is_following = Following.objects.filter(
                        user=request.user,
                        following=profile.user
                    ).exists()
                    
                    if not is_following :
                        if not profile.privacy.show_email:
                            data['user']['email'] = None
                        
                        if not profile.privacy.show_photo:
                            data['photo'] = None

                        if not profile.privacy.show_bio:
                            data['bio'] = None

                        if not profile.privacy.show_location:
                            data['location'] = None
                        
                        if not profile.privacy.show_social_links:
                            data['social_links'] = None
        return data

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'is_public',
            'bio',
            'photo',
            'location',
            'social_links',
        ]
