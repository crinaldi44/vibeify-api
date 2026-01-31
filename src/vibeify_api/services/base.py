"""Base service for business logic layer."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Generic, List, TypeVar, Optional, Type, Any

import httpx
from querymate import Querymate
from sqlmodel import SQLModel

from vibeify_api.core.context import get_current_user_from_context, require_current_user
from vibeify_api.core.database import AsyncSessionLocal
from vibeify_api.core.exceptions import NotFoundError
from vibeify_api.core.logging import get_logger
from vibeify_api.models.user import User
from vibeify_api.repository.base import BaseRepository
from vibeify_api.schemas.discovery import ProviderDiscoveryError, ProviderDiscoveryRequest
from vibeify_api.schemas.responses import ProviderDiscoveryResult

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseService(Generic[ModelType]):
    """Generic base service for business logic operations.

    Combines repository layer with QueryMate for flexible querying.
    """

    def __init__(self, model: Type[ModelType]):
        """Initialize service with model.

        Args:
            model: SQLModel class
        """
        self.model = model
        self.repository = BaseRepository(model)
        self._logger = get_logger(self.__class__.__name__)

    async def get(self, id: int) -> ModelType:
        """Get a single record by ID.

        Args:
            id: Record identifier

        Returns:
            Model instance

        Raises:
            NotFoundError: If record not found
        """
        result = await self.repository.get(id)
        if result is None:
            model_name = self.model.__name__
            raise NotFoundError(model_name, id)
        return result

    async def create(self, obj_in: ModelType | dict[str, Any]) -> ModelType:
        """Create a new record.

        Args:
            obj_in: Model instance or dictionary of attributes

        Returns:
            Created model instance
        """
        return await self.repository.create(obj_in)

    async def update(
        self,
        id: int,
        obj_in: ModelType | dict[str, Any],
    ) -> ModelType:
        """Update a record by ID.

        Args:
            id: Record identifier
            obj_in: Model instance or dictionary of attributes to update

        Returns:
            Updated model instance

        Raises:
            NotFoundError: If record not found
        """
        result = await self.repository.update(id, obj_in)
        if result is None:
            model_name = self.model.__name__
            raise NotFoundError(model_name, id)
        return result

    async def delete(self, id: int) -> None:
        """Delete a record by ID.

        Args:
            id: Record identifier

        Raises:
            NotFoundError: If record not found
        """
        deleted = await self.repository.delete(id)
        if not deleted:
            model_name = self.model.__name__
            raise NotFoundError(model_name, id)

    async def exists(self, id: int) -> bool:
        """Check if a record exists by ID.

        Args:
            id: Record identifier

        Returns:
            True if exists, False otherwise
        """
        return await self.repository.exists(id)

    async def query(
        self,
        query: Querymate,
    ) -> list[ModelType]:
        """Query records using QueryMate.

        Args:
            query: QueryMate instance with filters, sort, select, etc.

        Returns:
            List of serialized model instances
        """
        return await self.repository.query(query)

    async def list(
        self,
        query: Querymate,
    ) -> Any:
        """Query records with pagination using QueryMate.

        Args:
            query: QueryMate instance with filters, sort, select, etc.

        Returns:
            Paginated response with items and pagination metadata
        """
        return await self.repository.query_paginated(query)

    async def query_raw(
        self,
        query: Querymate,
    ) -> List[ModelType]:
        """Query records using QueryMate, returning raw model instances.

        Args:
            query: QueryMate instance with filters, sort, select, etc.

        Returns:
            List of model instances (not serialized)
        """
        return await self.repository.query_raw(query)
    
    def get_current_user(self) -> Optional[User]:
        """Get current user from request context.
        
        Returns:
            Current user or None if not authenticated
        """
        return get_current_user_from_context()
    
    def require_current_user(self) -> User:
        """Get current user from context, raising error if not set.
        
        Returns:
            Current user instance
            
        Raises:
            AuthenticationError: If no user in context
        """
        return require_current_user()


class BaseDiscoveryService(ABC):
    """Base for provider discovery services. Owns error handling; subclasses implement success normalization."""

    def __init__(self, *, client: Any) -> None:
        """Initialize with a provider client (context manager with .provider and .fetch(request))."""
        self._client = client

    @staticmethod
    def _safe_text(resp: httpx.Response) -> str:
        """Return response body text for error details, capped at 2000 chars."""
        try:
            txt = resp.text or ""
        except Exception:
            return ""
        return txt[:2000]

    def _is_missing_api_key(self) -> bool:
        """Return True if the client has no API key. Subclasses may override."""
        return not getattr(self._client, "_api_key", None)

    def _error_result(
        self,
        code: str,
        message: str,
        details: str | None = None,
    ) -> ProviderDiscoveryResult:
        """Build a failed ProviderDiscoveryResult."""
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=[],
            error=ProviderDiscoveryError(code=code, message=message, details=details),
        )

    async def _execute_fetch(
        self,
        coro: Callable[[], Awaitable[httpx.Response]],
        normalizer: Callable[[httpx.Response], Awaitable[ProviderDiscoveryResult]],
    ) -> ProviderDiscoveryResult:
        """Run fetch coroutine; on 2xx call normalizer(resp), on error return ProviderDiscoveryResult."""
        async with self._client:
            try:
                resp = await coro()
            except ValueError as e:
                if "API key" in str(e):
                    return self._error_result("missing_api_key", str(e))
                raise
            except httpx.TimeoutException as e:
                return self._error_result("timeout", "Request timed out", str(e))
            except httpx.HTTPError as e:
                return self._error_result("http_error", "HTTP request failed", str(e))

            if 200 <= resp.status_code < 300:
                return await normalizer(resp)

            if resp.status_code in (401, 403):
                return self._error_result(
                    "auth_error",
                    "Authentication failed.",
                    self._safe_text(resp),
                )
            if resp.status_code == 429:
                return self._error_result(
                    "rate_limited",
                    "Rate limit exceeded.",
                    self._safe_text(resp),
                )
            if 500 <= resp.status_code < 600:
                return self._error_result(
                    "provider_error",
                    f"Request failed (status={resp.status_code}).",
                    self._safe_text(resp),
                )
            return self._error_result(
                "provider_error",
                f"Request failed (status={resp.status_code}).",
                self._safe_text(resp),
            )
