from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import ValidationError, UnauthorizedError, NotFoundError
from app.core.logging import logger
from datetime import datetime, timezone
import traceback

def create_error_envelope(code: str, message: str, path: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": path,
        }
    }

HTTP_STATUS_TO_CODE_MAP = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    status.HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    status.HTTP_504_GATEWAY_TIMEOUT: "GATEWAY_TIMEOUT",
}

def register_exception_handlers(app: FastAPI):

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.info(f"ValidationError on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_envelope("VALIDATION_ERROR", str(exc), request.url.path),
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_error_handler(request: Request, exc: UnauthorizedError):
        logger.info(f"UnauthorizedError on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=create_error_envelope("UNAUTHORIZED", str(exc), request.url.path),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        logger.info(f"NotFoundError on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=create_error_envelope("NOT_FOUND", str(exc), request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        logger.info(f"RequestValidationError on {request.url.path}")
        # Simplistic mapping of pydantic errors for display
        messages = []
        for err in exc.errors():
            loc = ".".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "")
            messages.append(f"{loc}: {msg}" if loc else msg)
        message = "; ".join(messages)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_envelope("UNPROCESSABLE_ENTITY", message, request.url.path),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code >= 500:
            logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
        else:
            logger.info(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
        
        # Use deterministic mapping map
        error_code = HTTP_STATUS_TO_CODE_MAP.get(exc.status_code)
        if not error_code:
            error_code = "UNKNOWN_CLIENT_ERROR" if 400 <= exc.status_code < 500 else "UNKNOWN_SERVER_ERROR"

        # Special casing for HTTP exceptions that provide headers
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_envelope(error_code, str(exc.detail), request.url.path),
            headers=headers
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception on {request.url.path}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_envelope("INTERNAL_SERVER_ERROR", "An unexpected internal error occurred.", request.url.path),
        )
