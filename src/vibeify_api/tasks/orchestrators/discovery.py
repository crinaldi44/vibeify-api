"""Discovery orchestrator task.

Enqueues crawl jobs for a provided list of URLs.
"""

from __future__ import annotations

from typing import Optional

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.logging import get_logger
from vibeify_api.tasks.jobs.discovery import crawl_page

logger = get_logger(__name__)


@celery_app.task(name="tasks.discovery.orchestrate")
def orchestrate_discovery(
    urls: list[str],
    data_origin: str,
    target_application: Optional[str] = None,
    crawl: str = "CC-MAIN-2025-51",
    user_id: Optional[int] = None,
) -> dict:
    logger.debug("[ORCHESTRATOR]: Starting discovery orchestrator...")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_urls: list[str] = []
    for u in urls:
        if not u or u in seen:
            continue
        seen.add(u)
        unique_urls.append(u)

    # We enqueue all unique URLs; the job itself will use Postgres+digest checks
    # to decide whether to download/persist.
    for u in unique_urls:
        crawl_page.delay(
            url=u,
            data_origin=data_origin,
            target_application=target_application,
            crawl=crawl,
            user_id=user_id,
        )

    logger.debug(f"[ORCHESTRATOR]: Enqueued {len(unique_urls)} crawl jobs")

    return {
        "input_urls": len(urls),
        "unique_urls": len(unique_urls),
        "enqueued_jobs": len(unique_urls),
    }

