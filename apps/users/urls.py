from django.urls import path
from apps.users.views.user import (
    UserReadViews,
    UserSignupViews,
    UserLoginViews,
    UserUpdateViews,
    UserPasswordForgotViews,
    UserPasswordResetViews,
    UserDeleteViews,
)
from apps.users.views.token_refresh import CustomTokenRefreshView


app_name = 'users'


urlpatterns = [
    path(
        '', 
        UserReadViews.as_view()
    ),
    path(
        'signup', 
        UserSignupViews.as_view()
    ),
    path(
        'login', 
        UserLoginViews.as_view()
    ),
    path(
        'update', 
        UserUpdateViews.as_view()
    ),
    path(
        'delete', 
        UserDeleteViews.as_view()
    ),
    path(
        'password-forgot', 
        UserPasswordForgotViews.as_view()
    ),
    path(
        'password-reset', 
        UserPasswordResetViews.as_view()
    ),
    path(
        'token/refresh', 
        CustomTokenRefreshView.as_view(), 
        name='token_refresh'
    ),

]