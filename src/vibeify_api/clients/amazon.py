from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from vibeify_api.clients.base import BaseScrapingClient
from vibeify_api.schemas.discovery import DiscoveryRequest
from vibeify_api.services.http_client import HttpClientService


class AmazonClient(BaseScrapingClient[str]):
    origin = "amazon"

    async def scrape(self, request: DiscoveryRequest, http: HttpClientService) -> str:
        # Note: Amazon is hostile to scraping; keep this as a safe/standardized example.
        # A real implementation should use proper compliance, rate limiting, and parsing.
        url = f"https://www.amazon.com/s?k={quote_plus(request.query)}&ref=nb_sb_noss_2"

        try:
            resp = await http.get(url, headers=self._standard_headers())
            # Don't raise on non-2xx; return a standardized summary string.
            snippet = (resp.text or "")[:2000]
            return f"{url}\nstatus={resp.status_code}\n{snippet}"
        except httpx.TimeoutException:
            return f"{url}\nerror=timeout"
        except httpx.HTTPError as e:
            return f"{url}\nerror=http_error\ndetail={str(e)}"