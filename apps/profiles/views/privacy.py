from . import version_aware_dispatch
from apps.profiles.api.v1_0.views.privacy import(
    PrivacyReadApi as v1_PrivacyReadApi,
    PrivacyUpdateApi as v1_PrivacyUpdateApi,
)
from apps.profiles.api.v2_0.views.privacy import(
    PrivacyReadApi as v2_PrivacyReadApi,
    PrivacyUpdateApi as v2_PrivacyUpdateApi,
)

# Create your views here.

PrivacyReadViews = version_aware_dispatch({
    '1.0': v1_PrivacyReadApi,
    '2.0': v2_PrivacyReadApi      
})

PrivacyUpdateViews = version_aware_dispatch({
    '1.0': v1_PrivacyUpdateApi,
    '2.0': v2_PrivacyUpdateApi
})
