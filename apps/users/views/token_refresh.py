from rest_framework_simplejwt.views import TokenRefreshView
from apps.base.serializers import CustomTokenRefreshSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer