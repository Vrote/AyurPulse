from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP errors (400, 404, 415, 500 etc.) with a clean JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (e.g. missing required fields)."""
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Validation error"
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": message,
            "detail": str(errors),
        }
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — logs traceback, returns 500."""
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected server error occurred. Please try again.",
        }
    )