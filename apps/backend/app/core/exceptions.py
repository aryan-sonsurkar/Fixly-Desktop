from fastapi import Request
from fastapi.responses import JSONResponse


class FixlyError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(FixlyError):
    status_code = 404
    error_code = "NOT_FOUND"
    detail = "Resource not found"


class AuthenticationError(FixlyError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    detail = "Authentication failed"


class ValidationError(FixlyError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    detail = "Validation failed"


class AIProviderUnavailableError(FixlyError):
    status_code = 503
    error_code = "AI_UNAVAILABLE"
    detail = "AI provider is currently unavailable"


async def fixly_exception_handler(request: Request, exc: FixlyError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.error_code, "status": exc.status_code},
    )
