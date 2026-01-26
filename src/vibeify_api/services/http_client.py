"""Shared async HTTP client service (standardized defaults)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import httpx


class HttpClientService:
    """Thin wrapper around httpx.AsyncClient with sensible defaults."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        headers: Optional[Mapping[str, str]] = None,
        follow_redirects: bool = True,
    ) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers=dict(headers or {}),
            follow_redirects=follow_redirects,
        )

    async def __aenter__(self) -> "HttpClientService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
        data: Any = None,
    ) -> httpx.Response:
        return await self._client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            json=json,
            data=data,
        )

    async def get(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        return await self.request("GET", url, params=params, headers=headers)

