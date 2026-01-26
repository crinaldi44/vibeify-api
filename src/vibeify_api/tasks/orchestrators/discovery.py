"""Discovery orchestrator task.

Enqueues crawl jobs for a provided list of URLs.
"""

from __future__ import annotations

import re
from typing import Optional

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.asyncio_runner import run
from vibeify_api.core.logging import get_logger
from vibeify_api.services.crawled_page import CrawledPageService
from vibeify_api.tasks.jobs.discovery import crawl_page, crawl_page_hit

logger = get_logger(__name__)


@celery_app.task(name="tasks.discovery.orchestrate")
def orchestrate_discovery(
    urls: list[str],
    data_origin: str,
    target_application: Optional[str] = None,
    crawl: str = "CC-MAIN-2025-51",
    user_id: Optional[int] = None,
    seed_url: Optional[str] = None,
    match_type: str = "prefix",
    max_urls: int = 500,
    page_size: int = 1000,
    url_regex: Optional[str] = None,
) -> dict:
    logger.debug("[ORCHESTRATOR]: Starting discovery orchestrator...")

    service = CrawledPageService()

    # Combine explicit URLs + optional seed URL
    requested: list[str] = list(urls or [])
    if seed_url:
        requested.append(seed_url)

    # Deduplicate while preserving order
    seen_req: set[str] = set()
    unique_requested: list[str] = []
    for u in requested:
        if not u or u in seen_req:
            continue
        seen_req.add(u)
        unique_requested.append(u)

    regex = re.compile(url_regex) if url_regex else None

    exact_urls: list[str] = []
    discovered_hits: list[dict] = []

    for u in unique_requested:
        # If it looks like a wildcard/pattern, expand via CDX.
        if "*" in u or (seed_url and u == seed_url and match_type != "exact"):
            hits = run(
                service.discover_common_crawl_hits(
                    seed_url=u,
                    crawl=crawl,
                    match_type=match_type,
                    max_urls=max_urls,
                    page_size=page_size,
                    timeout_seconds=30,
                )
            )
            for h in hits:
                url_val = h.get("url")
                if not url_val:
                    continue
                if regex and not regex.search(url_val):
                    continue
                discovered_hits.append(h)
        else:
            exact_urls.append(u)

    # Enqueue discovered hits (pre-resolved WARC record pointers)
    enqueued = 0
    for h in discovered_hits:
        crawl_page_hit.delay(
            url=h["url"],
            data_origin=data_origin,
            target_application=target_application,
            crawl=crawl,
            user_id=user_id,
            warc_filename=h["warc_filename"],
            warc_offset=h["warc_offset"],
            warc_length=h["warc_length"],
            digest=h.get("digest"),
        )
        enqueued += 1

    # Enqueue exact URLs; the job itself will do a CDX exact lookup
    for u in exact_urls:
        crawl_page.delay(
            url=u,
            data_origin=data_origin,
            target_application=target_application,
            crawl=crawl,
            user_id=user_id,
        )
        enqueued += 1

    logger.debug(
        "[ORCHESTRATOR]: Enqueued %s jobs (%s discovered hits, %s exact URLs)",
        enqueued,
        len(discovered_hits),
        len(exact_urls),
    )

    return {
        "input_urls": len(urls or []),
        "seed_url": seed_url,
        "requested": len(unique_requested),
        "exact_urls": len(exact_urls),
        "discovered_urls": len(discovered_hits),
        "enqueued_jobs": enqueued,
    }

