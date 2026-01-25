"""Celery tasks module."""
from vibeify_api.core.celery_app import celery_app

# Import tasks to register them with Celery
from vibeify_api.tasks.example import hello_world, process_data  # noqa: F401
from vibeify_api.tasks.orchestrators.discovery import orchestrate_discovery  # noqa: F401
from vibeify_api.tasks.jobs.discovery import crawl_page  # noqa: F401

# Example: from vibeify_api.tasks.reports import generate_daily_report

__all__ = ["celery_app"]
