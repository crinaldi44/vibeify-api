"""Example Celery tasks for demonstration."""
from datetime import datetime

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="tasks.example.hello_world")
def hello_world(name: str = "World") -> dict:
    """Example task that returns a greeting.

    Args:
        name: Name to greet

    Returns:
        Dictionary with greeting message and timestamp
    """
    logger.info(f"Hello {name} task executed")
    return {
        "message": f"Hello, {name}!",
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery_app.task(name="tasks.example.process_data")
def process_data(data: dict) -> dict:
    """Example task that processes data.

    Args:
        data: Data to process

    Returns:
        Processed data with metadata
    """
    logger.info(f"Processing data: {data}")
    # Simulate processing
    processed = {
        **data,
        "processed": True,
        "processed_at": datetime.utcnow().isoformat(),
    }
    return processed
