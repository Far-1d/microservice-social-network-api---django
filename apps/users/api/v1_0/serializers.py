from rest_framework import serializers
from apps.users.models import User
from django.contrib.auth.hashers import make_password
from apps.relationships.models import Following

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'slug']

    def to_representation(self, instance):
        request = self.context.get('request')
        try:
            profile = instance.profile
            privacy = profile.privacy
        except:
            return super().to_representation(instance)
        
        data = super().to_representation(instance)
        
        if not profile.is_public and not privacy.show_email and instance != request.user:
            
            # check following
            is_following = Following.objects.filter(
                user=request.user,
                following=instance
            ).exists()
            
            if not is_following :
                data['email'] = None
        
        return data

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        data['slug'] = self.slugify_username(data['username'])
        data['password'] = make_password(data['password'])
        return data

    def slugify_username(self, username):
        from django.utils.text import slugify
        return slugify(username)
    
class UserLoginSerializer(serializers.Serializer):
    login_identifier = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

class UserPasswordForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()

class UserPasswordResetSerializer(serializers.Serializer):
    code = serializers.CharField()
    password = serializers.CharField()

class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)
    
