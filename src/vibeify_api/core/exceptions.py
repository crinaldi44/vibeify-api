"""Custom exceptions for the application."""
from fastapi import HTTPException, status


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
