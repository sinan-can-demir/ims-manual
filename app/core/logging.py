import logging
import sys
import time
import uuid

from pythonjsonlogger.json import JsonFormatter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def setup_logger():
    # create a logger for the inventory management system
    logger = logging.getLogger("ims")
    logger.setLevel(logging.INFO)

    # create a stream handler to output logs to stdout
    handler = logging.StreamHandler(sys.stdout)

    # define a log format
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    # set the formatter for the handler and add the handler to the logger
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)

    # return the configured
    return logger


logger = setup_logger()

# Requests hit repeatedly by infra (Docker HEALTHCHECK, Prometheus scrapes)
# are excluded from the access log below to avoid drowning out real traffic.
_ACCESS_LOG_EXEMPT_PATHS = {"/health", "/metrics"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one structured "request_completed" event per request, tagged with
    a request ID so a single request's log lines can be correlated."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        if request.url.path not in _ACCESS_LOG_EXEMPT_PATHS:
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
        return response
