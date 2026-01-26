"""Discovery service: routes requests to origin-specific scrapers concurrently."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from vibeify_api.clients.amazon import AmazonClient
from vibeify_api.clients.base import BaseScrapingClient
from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import (
    DiscoveryError,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryResult,
)
from vibeify_api.services.http_client import HttpClientService


class DiscoveryService:
    """Orchestrates discovery scraping across origins with standardized results."""

    def __init__(
        self,
        *,
        scrapers: dict[str, BaseScrapingClient[Any]] | None = None,
        max_concurrency: int = 10,
    ) -> None:
        self._logger = get_logger(self.__class__.__name__)
        self._scrapers: dict[str, BaseScrapingClient[Any]] = scrapers or {
            AmazonClient.origin: AmazonClient(),
        }
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def discover(self, requests: list[DiscoveryRequest]) -> DiscoveryResponse:
        """Concurrently process discovery requests and return standardized results."""
        async with HttpClientService() as http:
            coros = [self._discover_one(req, http=http) for req in requests]
            results = await asyncio.gather(*coros)
        return DiscoveryResponse(results=results)

    async def _discover_one(
        self,
        request: DiscoveryRequest,
        *,
        http: HttpClientService,
    ) -> DiscoveryResult:
        origin = request.origin.lower().strip()
        scraper = self._scrapers.get(origin)
        if scraper is None:
            return DiscoveryResult(
                origin=origin,
                query=request.query,
                ok=False,
                data=None,
                error=DiscoveryError(
                    code="unknown_origin",
                    message=f"Unsupported origin '{origin}'",
                ),
            )

        async with self._semaphore:
            try:
                payload = await scraper.scrape(request, http=http)
                # Standardize: always return dict-like data; wrap non-dicts.
                data: dict[str, Any]
                if isinstance(payload, dict):
                    data = payload
                else:
                    data = {"result": payload}

                return DiscoveryResult(
                    origin=origin,
                    query=request.query,
                    ok=True,
                    data=data,
                    error=None,
                )
            except httpx.TimeoutException as e:
                self._logger.warning("Discovery scrape timeout", extra={"origin": origin})
                return DiscoveryResult(
                    origin=origin,
                    query=request.query,
                    ok=False,
                    data=None,
                    error=DiscoveryError(code="timeout", message="Scrape timed out", details=str(e)),
                )
            except httpx.HTTPError as e:
                self._logger.warning("Discovery HTTP error", extra={"origin": origin})
                return DiscoveryResult(
                    origin=origin,
                    query=request.query,
                    ok=False,
                    data=None,
                    error=DiscoveryError(code="http_error", message="HTTP request failed", details=str(e)),
                )
            except Exception as e:
                self._logger.exception("Discovery scrape failed", extra={"origin": origin})
                return DiscoveryResult(
                    origin=origin,
                    query=request.query,
                    ok=False,
                    data=None,
                    error=DiscoveryError(code="scrape_failed", message="Scrape failed", details=str(e)),
                )

