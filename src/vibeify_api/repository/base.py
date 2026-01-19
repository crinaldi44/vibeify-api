"""Base repository for database operations."""
from typing import Generic, TypeVar, Optional, Type, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Generic repository base class for database operations.

    Provides common CRUD operations that can be extended by specific repositories.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize repository with model and session.

        Args:
            model: SQLModel class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            id: Record identifier

        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
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
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: ModelType | dict[str, Any]) -> ModelType:
        """Create a new record.

        Args:
            obj_in: Model instance or dictionary of attributes

        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

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
        db_obj = await self.get(id)
        if not db_obj:
            return None

        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        """Delete a record by ID.

        Args:
            id: Record identifier

        Returns:
            True if deleted, False if not found
        """
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.commit()
        return True

    async def exists(self, id: int) -> bool:
        """Check if a record exists by ID.

        Args:
            id: Record identifier

        Returns:
            True if exists, False otherwise
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total number of records.

        Returns:
            Total count
        """
        query = select(self.model)
        result = await self.session.execute(query)
        return len(list(result.scalars().all()))
