"""Base service for business logic layer."""
from typing import Generic, List, TypeVar, Optional, Type, Any

from querymate import Querymate
from sqlmodel import SQLModel

from vibeify_api.core.database import AsyncSessionLocal
from vibeify_api.core.exceptions import NotFoundError
from vibeify_api.repository.base import BaseRepository

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
