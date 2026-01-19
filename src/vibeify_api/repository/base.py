"""Base repository for database operations."""
from typing import Generic, TypeVar, Optional, Type, Any

from sqlalchemy import select
from sqlmodel import SQLModel

from vibeify_api.core.database import AsyncSessionLocal

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Generic repository base class for database operations.

    Provides common CRUD operations that can be extended by specific repositories.
    Manages its own database session lifecycle.
    """

    def __init__(self, model: Type[ModelType]):
        """Initialize repository with model.

        Args:
            model: SQLModel class
        """
        self.model = model

    async def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            id: Record identifier

        Returns:
            Model instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(self.model).where(self.model.id == id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

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
        async with AsyncSessionLocal() as session:
            query = select(self.model).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def create(self, obj_in: ModelType | dict[str, Any]) -> ModelType:
        """Create a new record.

        Args:
            obj_in: Model instance or dictionary of attributes

        Returns:
            Created model instance
        """
        async with AsyncSessionLocal() as session:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = obj_in

            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj

    async def query(self, query):
        async with AsyncSessionLocal() as session:
            return await query.run_async(session, self.model)

    async def query_paginated(self, query):
        async with AsyncSessionLocal() as session:
            return await query.run_async_paginated(session, self.model)

    async def query_raw(self, query):
        async with AsyncSessionLocal() as session:
            return await query.run_raw_async(session, self.model)

    async def update(
        self,
        id: int,
        obj_in: ModelType | dict[str, Any],
    ) -> Optional[ModelType]:
        """Update a record by ID.

        Args:
            id: Record identifier
            obj_in: Model instance or dictionary of attributes to update

        Returns:
            Updated model instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(self.model).where(self.model.id == id)
            result = await session.execute(query)
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return None

            update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj

    async def delete(self, id: int) -> bool:
        """Delete a record by ID.

        Args:
            id: Record identifier

        Returns:
            True if deleted, False if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(self.model).where(self.model.id == id)
            result = await session.execute(query)
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return False

            await session.delete(db_obj)
            await session.commit()
            return True

    async def exists(self, id: int) -> bool:
        """Check if a record exists by ID.

        Args:
            id: Record identifier

        Returns:
            True if exists, False otherwise
        """
        async with AsyncSessionLocal() as session:
            query = select(self.model).where(self.model.id == id)
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total number of records.

        Returns:
            Total count
        """
        async with AsyncSessionLocal() as session:
            query = select(self.model)
            result = await session.execute(query)
            return len(list(result.scalars().all()))
