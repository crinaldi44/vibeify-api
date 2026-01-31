"""Serper provider client.

Docs: https://serper.dev/
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.base import ProviderClient
from vibeify_api.core.config import get_settings
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest

_API_KEY_UNSET: Any = object()


class SerperClient(ProviderClient):
    provider = "serper"

    def __init__(
        self,
        *,
        api_key: Any = _API_KEY_UNSET,
        base_url: Optional[str] = None,
        _http: Any = None,
    ) -> None:
        settings = get_settings()
        timeout = settings.SERPER_TIMEOUT_SECONDS
        max_retries = settings.SERPER_MAX_RETRIES
        super().__init__(timeout_seconds=timeout, max_retries=max_retries, _http=_http)
        self._api_key = (
            getattr(settings, "SERPER_API_KEY", None) if api_key is _API_KEY_UNSET else api_key
        )
        self._base_url = (
            (base_url or getattr(settings, "SERPER_BASE_URL", "https://google.serper.dev")).rstrip("/")
        )

    async def fetch(self, request: ProviderDiscoveryRequest) -> httpx.Response:
        if not self._api_key:
            raise ValueError("Serper API key not configured (set SERPER_API_KEY).")

        search_type = (request.search_type or "search").strip().lower()
        endpoint = search_type if search_type else "search"
        url = f"{self._base_url}/{endpoint}"

        payload: dict[str, Any] = {"q": request.query}
        if request.num:
            payload["num"] = request.num
        if request.page:
            payload["page"] = request.page

        headers = {
            **self._standard_headers(),
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }

        return await self._request_with_retry("POST", url, headers=headers, json=payload)
