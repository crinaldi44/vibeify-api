"""User service for business logic."""
from datetime import timedelta

from querymate import Querymate

from vibeify_api.core.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from vibeify_api.core.security import create_access_token, get_password_hash, settings, verify_password
from vibeify_api.models.user import User
from vibeify_api.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from vibeify_api.services.base import BaseService
from vibeify_api.services.role import RoleService


class UserService(BaseService[User]):
    """Service for user-related business logic."""

    def __init__(self):
        """Initialize user service."""
        super().__init__(User)

    async def get_user_profile(self, user_id: int) -> UserResponse:
        """Get user profile.

        Args:
            user_id: User ID

        Returns:
            User profile
        """
        user = await self.query_raw(
            Querymate(filter={"id": {"eq": user_id}}, select=["*", {"role": ["*"]}]),
        )
        if len(user) == 0:
            raise NotFoundError("User not found")
        return user[0]

    async def login_user(self, user_data: UserLogin) -> Token:
        """Authenticate user and return JWT token.

        Args:
            user_data: User login credentials

        Returns:
            JWT access token

        Raises:
            AuthenticationError: If credentials are invalid
            AuthorizationError: If user is inactive
        """
        users = await self.query_raw(
            Querymate(filter={"email": {"eq": user_data.email}}, limit=1),
        )
        if len(users) == 0:
            raise AuthenticationError()

        user = users[0]

        # Verify password
        if not user.hashed_password or not verify_password(user_data.password, user.hashed_password):
            raise AuthenticationError()

        if not user.is_active:
            raise AuthorizationError("Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )

        return Token(access_token=access_token, token_type="bearer")

    async def register_user(self, user_data: UserRegister) -> UserResponse:
        """Register a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user instance (without password)

        Raises:
            AlreadyExistsError: If email or username already exists
            ValidationError: If validation fails
        """
        existing_user = await self.query_raw(
            Querymate(filter={"email": {"eq": user_data.email}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "email", user_data.email)

        existing_user = await self.query_raw(
            Querymate(filter={"username": {"eq": user_data.username}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "username", user_data.username)

        hashed_password = get_password_hash(user_data.password)

        role_service = RoleService()
        default_role = await role_service.get_by_name("User")
        if not default_role:
            raise ValidationError("Default user role not found. Please ensure roles are initialized.")

        try:
            user_create = User(
                    email=user_data.email,
                    username=user_data.username,
                    full_name=user_data.full_name,
                    hashed_password=hashed_password,
                    role_id=default_role.id,
                )
            await self.create(
                user_create
            )
        except ValueError as e:
            raise ValidationError(str(e)) from e

        return UserResponse.model_validate(user_create)

