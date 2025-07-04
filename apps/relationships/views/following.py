from . import version_aware_dispatch
from apps.relationships.api.v1_0.views.following import(
    FollowCountReadApi as v1_FollowCountReadApi,
    FollowerReadApi as v1_FollowerReadApi,
    FollowingReadApi as v1_FollowingReadApi,
    FollowToggleApi as v1_FollowToggleApi,
    FollowRequestApi as v1_FollowRequestApi,
    FollowRequestResponseApi as v1_FollowRequestResponseApi,
)

# Create your views here.

FollowingCountReadViews = version_aware_dispatch({
    '1.0': v1_FollowCountReadApi,
    '2.0': v1_FollowCountReadApi      
})

FollowerReadViews = version_aware_dispatch({
    '1.0': v1_FollowerReadApi,
    '2.0': v1_FollowerReadApi
})

FollowingReadViews = version_aware_dispatch({
    '1.0': v1_FollowingReadApi,
    '2.0': v1_FollowingReadApi
})

FollowToggleViews = version_aware_dispatch({
    '1.0': v1_FollowToggleApi,
    '2.0': v1_FollowToggleApi,
})

FollowRequestViews = version_aware_dispatch({
    '1.0': v1_FollowRequestApi,
    '2.0': v1_FollowRequestApi,
})

FollowRequestResponseViews = version_aware_dispatch({
    '1.0': v1_FollowRequestResponseApi,
    '2.0': v1_FollowRequestResponseApi,
})



# FollowRequestAcceptViews = version_aware_dispatch({
#     '1.0': v1_FollowRequestAcceptApi,
#     '2.0': v1_Api,
# })