"""Base service for business logic layer."""
from typing import Generic, TypeVar, Optional, Type, Any

from querymate import Querymate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from vibeify_api.repository.base import BaseRepository

ModelType = TypeVar("ModelType", bound=SQLModel)
IDType = TypeVar("IDType", int, str)


class BaseService(Generic[ModelType, IDType]):
    """Generic base service for business logic operations.

    Combines repository layer with QueryMate for flexible querying.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize service with model and session.

        Args:
            model: SQLModel class
            session: Async database session
        """
        self.model = model
        self.repository = BaseRepository(model, session)
        self.session = session

    async def get(self, id: IDType) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            id: Record identifier

        Returns:
            Model instance or None if not found
        """
        return await self.repository.get(id)

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Get multiple records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return await self.repository.get_multi(skip=skip, limit=limit)

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
        id: IDType,
        obj_in: ModelType | dict[str, Any],
    ) -> Optional[ModelType]:
        """Update a record by ID.

        Args:
            id: Record identifier
            obj_in: Model instance or dictionary of attributes to update

        Returns:
            Updated model instance or None if not found
        """
        return await self.repository.update(id, obj_in)

    async def delete(self, id: IDType) -> bool:
        """Delete a record by ID.

        Args:
            id: Record identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(id)

    async def exists(self, id: IDType) -> bool:
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
        return await query.run_async(self.session, self.model)

    async def query_paginated(
        self,
        query: Querymate,
    ) -> Any:
        """Query records with pagination using QueryMate.

        Args:
            query: QueryMate instance with filters, sort, select, etc.

        Returns:
            Paginated response with items and pagination metadata
        """
        return await query.run_paginated_async(self.session, self.model)

    async def query_raw(
        self,
        query: Querymate,
    ) -> list[ModelType]:
        """Query records using QueryMate, returning raw model instances.

        Args:
            query: QueryMate instance with filters, sort, select, etc.

        Returns:
            List of model instances (not serialized)
        """
        return await query.run_raw_async(self.session, self.model)
