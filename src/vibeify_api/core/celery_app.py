"""Celery application configuration."""
from datetime import timedelta

from celery import Celery

from vibeify_api.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "vibeify_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["vibeify_api.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Task routing
    task_routes={
        "vibeify_api.tasks.*": {"queue": "default"},
    },
    # Result expiration
    result_expires=3600,  # 1 hour
)

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "run-example-task-every-5-min": {
        "task": "tasks.example.hello_world",
        "schedule": timedelta(hours=1),
    },
}
