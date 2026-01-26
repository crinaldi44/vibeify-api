from __future__ import annotations

from typing import Any

from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import DiscoveryRequest
from vibeify_api.services.http_client import HttpClientService


class BaseScrapingClient[T]:

    def __init__(self):
        self._logger = get_logger(self.__class__.__name__)

    origin: str  # override in concrete clients (e.g. "amazon")

    async def scrape(self, request: DiscoveryRequest, http: HttpClientService) -> T:
        raise NotImplementedError("Method not implemented.")

    def _standard_headers(self) -> dict[str, str]:
        # Keep this conservative; scrapers can override as needed.
        return {
            "User-Agent": "vibeify-api-discovery/0.1 (+https://vibeify)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
