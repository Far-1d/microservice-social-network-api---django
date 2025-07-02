from . import version_aware_dispatch
from apps.profiles.api.v1_0.views.profile import(
    ProfileListApi as v1_ProfileListApi,
    ProfileReadApi as v1_ProfileReadApi,
    ProfileUpdateApi as v1_ProfileUpdateApi,
)

from apps.profiles.api.v2_0.views.profile import(
    ProfileListApi as v2_ProfileListApi,
    ProfileReadApi as v2_ProfileReadApi,
    ProfileUpdateApi as v2_ProfileUpdateApi,
)

# Create your views here.

ProfileListViews = version_aware_dispatch({
    '1.0': v1_ProfileListApi,
    '2.0': v2_ProfileListApi
})

ProfileReadViews = version_aware_dispatch({
    '1.0': v1_ProfileReadApi,
    '2.0': v2_ProfileReadApi
})

ProfileUpdateViews = version_aware_dispatch({
    '1.0': v1_ProfileUpdateApi,
    '2.0': v2_ProfileUpdateApi
})
