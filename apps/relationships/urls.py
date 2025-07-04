from django.urls import path
from apps.relationships.views.following import (
    FollowingCountReadViews,
    FollowerReadViews,
    FollowingReadViews,
    FollowRequestViews,
    FollowRequestResponseViews,
    FollowToggleViews
)

from apps.relationships.views.block import (
    BlockViews,
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
        'follow', 
        FollowToggleViews.as_view()
    ),
    path(
        'follow/<str:slug>', 
        FollowingCountReadViews.as_view()
    ),
    path(
        'follow/<str:slug>/followers', 
        FollowerReadViews.as_view()
    ),
    path(
        'follow/<str:slug>/followings', 
        FollowingReadViews.as_view()
    ),   

    path(
        'block', 
        BlockViews.as_view()
    ),
]