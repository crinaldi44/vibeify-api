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
        _http: Any = None,
    ) -> None:
        settings = get_settings()
        timeout = settings.SERPER_TIMEOUT_SECONDS
        max_retries = settings.SERPER_MAX_RETRIES
        super().__init__(timeout_seconds=timeout, max_retries=max_retries, _http=_http)
        self._api_key = settings.SERPER_API_KEY
        self._base_url = settings.SERPER_BASE_URL

    async def execute_request(
        self, method: str, url: str, *, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Low-level fetch: arbitrary URL with Serper auth. Uses retries."""
        if not self._api_key:
            raise ValueError("Serper API key not configured (set SERPER_API_KEY).")
        headers = {
            **self._standard_headers(),
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }
        return await self._request_with_retry(method, url, headers=headers, json=json, **kwargs)
