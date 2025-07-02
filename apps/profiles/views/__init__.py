from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from typing import Any

def version_aware_dispatch(view_classes):
    """
    Factory that returns a view class that dispatches to version-specific implementations
    """
    class VersionAwareView(APIView):
        renderer_classes = [JSONRenderer]
        
        def initialize_request(self, request, *args, **kwargs):
            # Ensure DRF request wrapping happens
            drf_request = super().initialize_request(request, *args, **kwargs)
            # Your version attachment logic here
            return drf_request
        
        def finalize(self, request, response):
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = 'application/json'
            response.renderer_context = {
                'view': self,
                'args': getattr(self, 'args', ()),
                'kwargs': getattr(self, 'kwargs', {}),
                'request': request
            }
            return response
        
        def dispatch(self, request, *args, **kwargs) -> Response | Any:
            try:
                version = getattr(request, 'api_version', '1.0')
                view_class = view_classes.get(version)
                
                if not view_class:
                    print("there was view class error, returning response ", version)
                    response = self.finalize(
                        request,
                        Response(
                            {'error': f'API version {version} not implemented'},
                            status=400
                        )
                    )
                    return response
                    
                response = view_class.as_view()(request, *args, **kwargs)

                # Ensure renderer is set if not already
                if not hasattr(response, 'accepted_renderer'):
                    response = self.finalize_response(request, response)

                return response
            
            except Exception as e:
                raise e
        
    return VersionAwareView