"""Role service for business logic."""
from querymate import Querymate

from vibeify_api.models.role import Role
from vibeify_api.services.base import BaseService


class RoleService(BaseService[Role]):
    """Service for role-related business logic."""

    def __init__(self):
        """Initialize role service."""
        super().__init__(Role)

    async def get_by_name(self, name: str) -> Role | None:
        """Get a role by name.

        Args:
            name: Role name

        Returns:
            Role instance or None if not found
        """
        results = await self.query_raw(
            Querymate(filter={"name": {"eq": name}}, limit=1)
        )
        return results[0] if results else None
