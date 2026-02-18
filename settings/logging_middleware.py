import time, uuid
import structlog
from settings.logging import get_logger


class LoggingMiddleware:
    """
    Logs every request with:
    - IP address + user 
    - Method, path, status code
    - Human-readable timestamp + duration
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        logger = get_logger("http")
        # Generate a unique request ID for tracing errors
        request_id = str(uuid.uuid4())[:8]

        # Extract who is making the request
        client_ip = self._get_client_ip(request)
        if request.user.is_authenticated:
            user_id = str(request.user.id)
        else:
            user_id = None

        # Bind context so all logs within this request share these fields
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            api_version=request.api_version,
            ip=client_ip,
            user_id=user_id or "anonymous",
            method=request.method,
            path=request.path,
        )

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = self.get_response(request)
            status_code = response.status_code
            

        except Exception as exc:
            logger.error(
                "request_failed",
                error=str(exc),
                exc_info=True,
            )
            raise

        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            if request.path not in ("/metrics", "/health"):
            
                log_fn = logger.warning if status_code >= 400 else logger.info
                log_fn(
                    "request_finished",
                    status_code=status_code,
                    duration_ms=duration_ms
                )
            
            return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

