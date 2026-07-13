"""
Global exception handlers for consistent API error responses.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("codepilot.exceptions")


def _error_response(status_code: int, message: str, error_code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error_code": error_code,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP {exc.status_code} on {request.url}: {exc.detail}")
        return _error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        field = " → ".join(str(l) for l in first.get("loc", []))
        msg = f"Validation error on '{field}': {first.get('msg', 'invalid input')}"
        logger.warning(f"Validation error on {request.url}: {msg}")
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=msg,
            error_code="VALIDATION_ERROR",
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.error(f"ValueError on {request.url}: {exc}")
        return _error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(exc),
            error_code="INVALID_INPUT",
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.url}: {exc}")
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_SERVER_ERROR",
        )
