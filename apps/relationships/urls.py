from django.urls import path
from apps.relationships.views.following import (
    FollowingCountReadViews,
    FollowerReadViews,
    FollowingReadViews,
    FollowRequestViews,
    FollowRequestResponseViews,
)

app_name = 'relationships'


urlpatterns = [
    path(
        'requests', 
        FollowRequestViews.as_view()
    ),
    path(
        'requests/response', 
        FollowRequestResponseViews.as_view()
    ),
    path(
        '<str:slug>', 
        FollowingCountReadViews.as_view()
    ),
    path(
        '<str:slug>/followers', 
        FollowerReadViews.as_view()
    ),
    path(
        '<str:slug>/followings', 
        FollowingReadViews.as_view()
    ),   
]