"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vibeify_api.api.v1.router import api_router
from vibeify_api.core.config import get_settings
from vibeify_api.core.database import close_db, init_db
from vibeify_api.core.exceptions import ServiceException
from vibeify_api.core.logging import get_logger, setup_logging
from vibeify_api.schemas.errors import ErrorResponse, ValidationErrorDetail

settings = get_settings()

setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException) -> JSONResponse:
    """Handle service layer exceptions with standardized error format.

    Args:
        request: FastAPI request object
        exc: ServiceException instance

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail or "An error occurred",
            status_code=exc.status_code,
            detail=exc.detail,
        ).model_dump(exclude_unset=True, by_alias=True),
        headers=exc.headers if hasattr(exc, "headers") and exc.headers else None,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
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
        headers=exc.headers if hasattr(exc, "headers") and exc.headers else None,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
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
        
        # Add to detail string
        error_messages.append(f"{field}: {message}")
        
        # Add structured message
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


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standardized error format.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSONResponse with standardized error format
    """
    # Only show detailed error in debug mode
    detail = str(exc) if settings.DEBUG else "An unexpected error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ).model_dump(exclude_unset=True, by_alias=True)
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Vibeify API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
