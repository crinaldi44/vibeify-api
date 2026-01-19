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


class UserService(BaseService[User]):
    """Service for user-related business logic."""

    def __init__(self):
        """Initialize user service."""
        super().__init__(User)

    async def query(self, query: Querymate) -> list[User]:
        return await super().query(query)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None if not found
        """
        results = await self.query_raw(
            Querymate(filter={"email": {"eq": email}}, limit=1)
        )
        return results[0] if results else None

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

        # Check if user is active
        if not user.is_active:
            raise AuthorizationError("Inactive user")

        # Create access token
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
        # Check if email exists
        existing_user = await self.query_raw(
            Querymate(filter={"email": {"eq": user_data.email}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "email", user_data.email)

        # Check if username exists
        existing_user = await self.query_raw(
            Querymate(filter={"username": {"eq": user_data.username}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "username", user_data.username)

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        try:
            user = await self.create(
                User(
                    email=user_data.email,
                    username=user_data.username,
                    full_name=user_data.full_name,
                    hashed_password=hashed_password,
                )
            )
        except ValueError as e:
            raise ValidationError(str(e)) from e

        return UserResponse.model_validate(user)

    async def create_user(
        self,
        email: str,
        username: str,
        full_name: str | None = None,
        hashed_password: str | None = None,
    ) -> User:
        """Create a new user (admin/internal use).

        Args:
            email: User email
            username: Username
            full_name: Full name (optional)
            hashed_password: Hashed password (optional)

        Returns:
            Created user instance

        Raises:
            AlreadyExistsError: If email or username already exists
            ValidationError: If validation fails
        """
        # Check if email exists
        existing_user = await self.query_raw(
            Querymate(filter={"email": {"eq": email}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "email", email)

        # Check if username exists
        existing_user = await self.query_raw(
            Querymate(filter={"username": {"eq": username}}, limit=1)
        )
        if existing_user:
            raise AlreadyExistsError("User", "username", username)

        # Create user
        try:
            user = await self.create(
                User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    hashed_password=hashed_password,
                )
            )
        except ValueError as e:
            raise ValidationError(str(e)) from e

        return user
