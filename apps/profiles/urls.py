from django.urls import path
from apps.profiles.views.profile import (
    ProfileListViews,
    ProfileReadViews,
    ProfileUpdateViews,
)
from apps.profiles.views.privacy import(
    PrivacyReadViews,
    PrivacyUpdateViews
)


app_name = 'profiles'


urlpatterns = [
    path(
        '', 
        ProfileListViews.as_view()
    ),
    path(
        'update', 
        ProfileUpdateViews.as_view()
    ),
    path(
        '<str:slug>', 
        ProfileReadViews.as_view()
    ),
    path(
        'privacy/update', 
        PrivacyUpdateViews.as_view()
    ),
    path(
        'privacy/<str:slug>', 
        PrivacyReadViews.as_view()
    ),
]