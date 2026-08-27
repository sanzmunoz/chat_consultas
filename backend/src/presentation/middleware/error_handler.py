import logging
from datetime import datetime, timezone
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger("riwi_chat.api")

async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    path = request.url.path

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        code = f"HTTP_{status_code}"
        message = str(exc.detail)
        details = None
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        code = "VALIDATION_ERROR"
        message = "Input validation failed."
        details = exc.errors()
    elif isinstance(exc, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        code = "BAD_REQUEST"
        message = str(exc)
        details = None
    elif isinstance(exc, PermissionError):
        status_code = status.HTTP_403_FORBIDDEN
        code = "FORBIDDEN"
        message = str(exc)
        details = None
    else:
        logger.exception(f"Unhandled error on {path} [correlation: {correlation_id}]: {exc}")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = "INTERNAL_SERVER_ERROR"
        message = "An unexpected internal server error occurred."
        details = None

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details
            },
            "path": path,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        headers={"X-Correlation-Id": correlation_id}
    )
