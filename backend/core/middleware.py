import json
import logging
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.audit")


class RequestAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique X-Request-ID to every HTTP request,
    tracks execution latency in milliseconds, and logs structured audit JSON entries.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Honor client-provided request ID or generate a cryptographic random UUID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.perf_counter()

        # Attach request_id to request state
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            log_payload = {
                "event": "http_request_error",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "duration_ms": duration_ms,
                "error": str(exc),
            }
            logger.error(json.dumps(log_payload))
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "microphone=(self), geolocation=(), camera=()"

        log_payload = {
            "event": "http_request_complete",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else "unknown",
            "duration_ms": duration_ms,
        }
        logger.info(json.dumps(log_payload))

        return response
