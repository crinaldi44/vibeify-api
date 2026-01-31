"""Provider clients are repository-style: build request, perform HTTP call, return raw response."""

from __future__ import annotations

import asyncio
import random
from typing import Any, Mapping, Optional

import httpx

from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest


class ProviderClient:
    """Repository-style client: builds the HTTP request and returns the raw response.
    Owns the HTTP client lifecycle (create on context enter, close on exit) and retries
    on 429, 5xx, timeout, and HTTPError. Subclasses should use _request_with_retry
    for the actual call when they want retries. Callers (provider services) handle
    response normalization and domain DTOs."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        headers: Optional[Mapping[str, str]] = None,
        max_retries: int = 2,
        _http: Any = None,
    ) -> None:
        self._logger = get_logger(self.__class__.__name__)
        self._timeout_seconds = timeout_seconds
        self._base_headers = dict(headers or {})
        self._max_retries = max_retries
        self._http = _http
        self._http_owned = False

    provider: str = ""

    async def __aenter__(self) -> "ProviderClient":
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout_seconds),
                headers={**self._standard_headers(), **self._base_headers},
                follow_redirects=True,
            )
            self._http_owned = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, tb: Any) -> None:
        if self._http_owned and self._http is not None:
            await self._http.aclose()
            self._http_owned = False

    async def execute_request(
        self, method: str, url: str, *, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform the HTTP call and return the raw response. May raise httpx exceptions."""
        raise NotImplementedError("Method not implemented.")

    async def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Perform the request with retries on 429, 5xx, timeout, and HTTPError."""
        last_exc: Optional[BaseException] = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._http.request(method, url, **kwargs)

                if 200 <= resp.status_code < 300:
                    return resp
                if resp.status_code in (401, 403):
                    return resp
                if resp.status_code == 429 or (500 <= resp.status_code < 600):
                    if attempt < self._max_retries:
                        await self._backoff(resp, attempt=attempt)
                        continue
                    return resp
                return resp
            except (httpx.TimeoutException, httpx.HTTPError) as e:
                last_exc = e
                if attempt < self._max_retries:
                    await self._backoff(None, attempt=attempt)
                    continue
                raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Unexpected retry loop exit")

    async def _backoff(self, resp: Optional[httpx.Response], *, attempt: int) -> None:
        """Sleep before retry; honor Retry-After when response is available."""
        if resp is not None:
            retry_after = resp.headers.get("retry-after")
            if retry_after:
                try:
                    seconds = float(retry_after)
                    await asyncio.sleep(min(60.0, max(0.0, seconds)))
                    return
                except ValueError:
                    pass
        await asyncio.sleep(min(30.0, 1.0 * (2**attempt)) + random.random() * 0.25)

    def _standard_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "vibeify-api-discovery/0.1 (+https://vibeify)",
            "Accept": "*/*",
        }
