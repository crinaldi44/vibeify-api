from vibeify_api.models.reports import Report
from vibeify_api.services import BaseService


class ReportService(BaseService[Report]):
    """Service for role-related business logic."""

    def __init__(self):
        """Initialize role service."""
        super().__init__(Report)
