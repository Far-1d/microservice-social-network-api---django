from apps.relationships.models import Following

def apply_privacy_v1(profile, request_user):
    """Apply privacy settings to profile data"""

    data = {
        'username': profile.user.username,
        'username_slug': profile.user.slug,
        'bio': profile.bio,
        'photo': profile.photo.url if profile.photo else None,
        'is_public': profile.is_public
    }

    if not profile.is_public:
        # filter only if the requesting user is neither the profile owner nor a staff member
        if not request_user.is_staff and profile.user != request_user :
            # check following
            is_following = Following.objects.filter(
                user=request_user,
                following=profile.user
            ).exists()
            
            if not is_following :
                if not profile.privacy.show_photo:
                    data['photo'] = None

                if not profile.privacy.show_bio:
                    data['bio'] = None

    
    return data


def apply_privacy_v2(profile, request_user):
    """Apply privacy settings to profile data"""

    data = {
        'username': profile.user.username,
        'username_slug': profile.user.slug,
        'bio': profile.bio,
        'photo': profile.photo.url if profile.photo else None,
        'is_public': profile.is_public,
        'location': profile.location,
        'social_links': profile.social_links
    }

    if not profile.is_public:
        # filter only if the requesting user is neither the profile owner nor a staff member
        if not request_user.is_staff and profile.user != request_user :
            # check following
            is_following = Following.objects.filter(
                user=request_user,
                following=profile.user
            ).exists()
            
            if not is_following :

                if not profile.privacy.show_photo:
                    data['photo'] = None

                if not profile.privacy.show_bio:
                    data['bio'] = None

                if not profile.privacy.show_location:
                    data['location'] = None
                
                if not profile.privacy.show_social_links:
                    data['social_links'] = None
            
    return data