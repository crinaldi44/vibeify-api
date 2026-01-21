"""Custom exceptions for the application."""
from fastapi import HTTPException, status
from starlette.responses import JSONResponse

from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.errors import ErrorResponse, ValidationErrorDetail


class ServiceException(HTTPException):
    """Base exception for service layer errors."""
    pass


class NotFoundError(ServiceException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID {identifier} not found",
        )


class AlreadyExistsError(ServiceException):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{resource} with {field} '{value}' already exists",
        )


class AuthenticationError(ServiceException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(ServiceException):
    """Raised when authorization fails."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ValidationError(ServiceException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

ERROR_RESPONSES = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                  "error": "An error occurred while processing the request.",
                  "statusCode": 500,
                  "detail": "Error",
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
      "model": ErrorResponse,
      "content": {
          "application/json": {
              "example": {
                  "error": "The requested resource was not found.",
                  "statusCode": 404,
                  "detail": "Error",
              }
          }
      }
    },
    status.HTTP_403_FORBIDDEN: {
      "model": ErrorResponse,
      "content": {
          "application/json": {
              "example": {
                  "error": "Access to the requested resource is forbidden.",
                  "statusCode": 403,
                  "detail": "Unauthorized",
              }
          }
      }
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
      "model": ErrorResponse,
      "content": {
            "application/json": {
                "example": {
                  "error": "An error occurred while processing the request.",
                  "statusCode": 422,
                  "detail": "body -> password: Field required",
                  "messages": [
                    {
                      "field": "body -> password",
                      "message": "Field required",
                      "type": "missing",
                      "location": [
                        "body",
                        "password"
                      ]
                    }
                  ]
                }
            }
        }
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                  "error": "An error occurred while processing the request.",
                  "statusCode": 400,
                  "detail": "body -> password: Field required",
                  "messages": [
                    {
                      "field": "body -> password",
                      "message": "Field required",
                      "type": "missing",
                      "location": [
                        "body",
                        "password"
                      ]
                    }
                  ]
                }
            }
        }
    }
}

logger = get_logger(__name__)

async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with standardized error format.

        Args:
            request: FastAPI request object
            exc: HTTPException instance

        Returns:
            JSONResponse with standardized error format
        """
    logger.debug(f"Unhandled exception: {exc}",
                 extra={
                     "path": request.url.path,
                     "method": request.method,
                 })
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail or "An error occurred",
            status_code=exc.status_code,
            detail=exc.detail,
        ).model_dump(exclude_unset=True, by_alias=True),
    )

async def request_validation_exception_handler(request, exc):
    """Handle request validation errors with standardized error format.

    Args:
        request: FastAPI request object
        exc: RequestValidationError instance

    Returns:
        JSONResponse with standardized error format
    """
    errors = exc.errors()
    error_messages = []
    messages = []

    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_type = error.get("type", "validation_error")

        error_messages.append(f"{field}: {message}")

        messages.append(ValidationErrorDetail(
            field=field,
            message=message,
            type=error_type,
            location=list(error["loc"]),
        ))

    detail = "; ".join(error_messages) if error_messages else "Validation error"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="An error occurred while processing the request.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            messages=messages
        ).model_dump(exclude_unset=True, by_alias=True)
    )
