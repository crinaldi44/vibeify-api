"""Discovery crawl job task.

Fetches a URL's HTML, stores it in S3, and writes a Postgres metadata record.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.logging import get_logger
from vibeify_api.services.crawled_page import CrawledPageService

logger = get_logger(__name__)


@celery_app.task(name="tasks.discovery.crawl_page")
def crawl_page(
    url: str,
    data_origin: str,
    target_application: Optional[str] = None,
    crawl: str = "CC-MAIN-2025-51",
    user_id: Optional[int] = None,
) -> dict:
    logger.info(f"Crawling URL via Common Crawl: {url}")
    service = CrawledPageService()
    return asyncio.run(
        service.fetch_from_common_crawl_and_persist(
            url=url,
            data_origin=data_origin,
            target_application=target_application,
            user_id=user_id,
            crawl=crawl,
        ),
    )

