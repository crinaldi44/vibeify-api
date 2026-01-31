"""Discovery crawl job task.

Fetches a URL's HTML, stores it in S3, and writes a Postgres metadata record.
"""

from __future__ import annotations

from typing import Optional

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.asyncio_runner import run
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
    try:
        return run(
            service.fetch_from_common_crawl_and_persist(
                url=url,
                data_origin=data_origin,
                target_application=target_application,
                user_id=user_id,
                crawl=crawl,
            ),
        )
    except Exception:
        logger.exception(
            "Discovery crawl failed",
            extra={
                "url": url,
                "data_origin": data_origin,
                "target_application": target_application,
                "crawl": crawl,
                "user_id": user_id,
            },
        )
        raise


@celery_app.task(name="tasks.discovery.crawl_page_hit")
def crawl_page_hit(
    url: str,
    data_origin: str,
    warc_filename: str,
    warc_offset: int,
    warc_length: int,
    digest: Optional[str] = None,
    target_application: Optional[str] = None,
    crawl: str = "CC-MAIN-2025-51",
    user_id: Optional[int] = None,
) -> dict:
    """
    Persist a page using a pre-resolved Common Crawl hit (CDX record).

    This avoids performing a second per-URL CDX lookup when the orchestrator
    already discovered the WARC filename/offset/length.
    """
    service = CrawledPageService()
    try:
        return run(
            service.fetch_from_common_crawl_hit_and_persist(
                url=url,
                data_origin=data_origin,
                target_application=target_application,
                user_id=user_id,
                crawl=crawl,
                warc_filename=warc_filename,
                warc_offset=warc_offset,
                warc_length=warc_length,
                digest=digest,
            )
        )
    except Exception:
        logger.exception(
            "Discovery crawl (hit) failed",
            extra={
                "url": url,
                "data_origin": data_origin,
                "target_application": target_application,
                "crawl": crawl,
                "user_id": user_id,
                "warc_filename": warc_filename,
                "warc_offset": warc_offset,
                "warc_length": warc_length,
                "digest": digest,
            },
        )
        raise

