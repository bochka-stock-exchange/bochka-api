import logging
import time
from json import JSONDecodeError

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        try:
            body = await request.json()
        except JSONDecodeError:
            body = "Not Included"
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed",
                extra={
                    "client_host": client_host,
                    "method": method,
                    "path": path,
                    "process_time": f"{process_time:.2f}ms",
                    "error": str(e),
                    "body": body if settings.DEBUG else "Not Included",
                },
            )
            raise

        process_time = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        log_level = "warning" if status_code >= status.HTTP_400_BAD_REQUEST else "info"
        log_message = f"{method} {path} {status_code}"

        logger.log(
            getattr(logging, log_level.upper()),
            log_message,
            extra={
                "client_host": client_host,
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time": f"{process_time:.2f}ms",
                "type": "http",
                "body": body if settings.DEBUG else "Not Included",
            },
        )

        return response
