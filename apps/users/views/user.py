from . import version_aware_dispatch

from apps.users.api.v1_0.views import (
    UserReadApi  as V1_UserReadApi,
    UserSignupApi  as V1_UserSignupApi,
    UserLoginApi  as V1_UserLoginApi,
    UserPasswordForgotApi as V1_UserPasswordForgotApi,
    UserPasswordResetApi as V1_UserPasswordResetApi,
    UserUpdateApi as V1_UserUpdateApi,
    UserDeleteApi as V1_UserDeleteApi,
)

from apps.users.api.v2_0.views import (
    UserSignupApi  as V2_UserSignupApi,
)

UserReadViews = version_aware_dispatch({
    '1.0': V1_UserReadApi,
    '2.0': V1_UserReadApi
})

UserSignupViews = version_aware_dispatch({
    '1.0': V1_UserSignupApi,
    '2.0': V2_UserSignupApi
})

UserLoginViews = version_aware_dispatch({
    '1.0': V1_UserLoginApi,
    '2.0': V1_UserLoginApi          # no new feature yet
})

UserPasswordForgotViews = version_aware_dispatch({
    '1.0': V1_UserPasswordForgotApi,
    '2.0': V1_UserPasswordForgotApi # no new feature yet
})

UserPasswordResetViews = version_aware_dispatch({
    '1.0': V1_UserPasswordResetApi,
    '2.0': V1_UserPasswordResetApi  # no new feature yet
})

UserUpdateViews = version_aware_dispatch({
    '1.0': V1_UserUpdateApi,
    '2.0': V1_UserUpdateApi         # no new feature yet
})

UserDeleteViews = version_aware_dispatch({
    '1.0': V1_UserDeleteApi,
    '2.0': V1_UserDeleteApi         # no new feature yet
})

