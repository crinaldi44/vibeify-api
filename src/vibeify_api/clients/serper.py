"""Serper provider client.

Docs: https://serper.dev/
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.base import ProviderClient
from vibeify_api.core.config import get_settings
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest


class SerperClient(ProviderClient):
    provider = "serper"

    def __init__(
        self,
        *,
        _http: Any = None,
    ) -> None:
        settings = get_settings()
        timeout = settings.SERPER_TIMEOUT_SECONDS
        max_retries = settings.SERPER_MAX_RETRIES
        super().__init__(timeout_seconds=timeout, max_retries=max_retries, _http=_http)
        self._api_key = settings.SERPER_API_KEY
        self._base_url = settings.SERPER_BASE_URL.rstrip("/")

    async def fetch(self, request: ProviderDiscoveryRequest) -> httpx.Response:
        if not self._api_key:
            raise ValueError("Serper API key not configured (set SERPER_API_KEY).")

        search_type = (request.search_type or "search").strip().lower()
        endpoint = search_type if search_type else "search"
        url = f"{self._base_url}/{endpoint}"

        q = request.query
        if request.site:
            q = f"site:{request.site} {q}".strip()

        payload: dict[str, Any] = {"q": q}
        if request.country:
            payload["gl"] = request.country
        if request.language:
            payload["hl"] = request.language
        if request.num:
            payload["num"] = request.num
        if request.page:
            payload["page"] = request.page
        if request.options:
            payload.update(request.options)

        headers = {
            **self._standard_headers(),
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }

        return await self._request_with_retry("POST", url, headers=headers, json=payload)
