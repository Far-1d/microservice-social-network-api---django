# apps/core/versioning_middleware.py
from django.conf import settings

class VersioningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_version = getattr(settings, 'API_DEFAULT_VERSION', '1.0')
        self.version_header = getattr(settings, 'API_VERSION_HEADER', 'X-API-Version')

    def __call__(self, request):
        # Extract version from header
        version = request.headers.get(self.version_header, self.default_version)
        
        # Attach version to request
        request.api_version = version
        
        response = self.get_response(request)

        # Only interfere with DRF APIView responses
        if hasattr(response, 'accepted_renderer') and response.accepted_renderer is None:
            from rest_framework.renderers import JSONRenderer
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = 'application/json'
            response.renderer_context = {}

        return response