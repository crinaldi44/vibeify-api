"""Serper provider client.

Docs/examples: https://serper.dev/
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Optional

import httpx

from vibeify_api.clients.base import ProviderClient
from vibeify_api.core.config import get_settings
from vibeify_api.schemas.discovery import ProviderDiscoveryError, ProviderDiscoveryRequest, ProviderSearchResult
from vibeify_api.schemas.responses import ProviderDiscoveryResult
from vibeify_api.services.http_client import HttpClientService


class SerperClient(ProviderClient[ProviderDiscoveryResult]):
    provider = "serper"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_concurrency: Optional[int] = None,
        min_interval_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        super().__init__()
        settings = get_settings()

        self._api_key = api_key or getattr(settings, "SERPER_API_KEY", None)
        self._base_url = (base_url or getattr(settings, "SERPER_BASE_URL", "https://google.serper.dev")).rstrip("/")

        self._max_concurrency = int(
            getattr(settings, "SERPER_MAX_CONCURRENCY", 5) if max_concurrency is None else max_concurrency
        )
        self._min_interval_seconds = float(
            getattr(settings, "SERPER_MIN_INTERVAL_SECONDS", 0.0)
            if min_interval_seconds is None
            else min_interval_seconds
        )
        self._max_retries = int(getattr(settings, "SERPER_MAX_RETRIES", 2) if max_retries is None else max_retries)

        self._semaphore = asyncio.Semaphore(self._max_concurrency)
        self._rate_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def search(self, request: ProviderDiscoveryRequest, http: HttpClientService) -> ProviderDiscoveryResult:
        if not self._api_key:
            return ProviderDiscoveryResult(
                provider=self.provider,
                query=request.query,
                ok=False,
                results=[],
                raw=None,
                error=ProviderDiscoveryError(
                    code="missing_api_key",
                    message="Serper API key not configured (set SERPER_API_KEY).",
                ),
            )

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

        last_err: Optional[str] = None
        for attempt in range(self._max_retries + 1):
            try:
                async with self._semaphore:
                    await self._throttle()
                    resp = await http.request("POST", url, headers=headers, json=payload)

                if 200 <= resp.status_code < 300:
                    body = resp.json()
                    results = self._normalize_results(body, preferred_bucket=endpoint)
                    return ProviderDiscoveryResult(
                        provider=self.provider,
                        query=request.query,
                        ok=True,
                        results=results,
                        raw=body if request.include_raw else None,
                        error=None,
                    )

                # Auth/config issues: don't retry.
                if resp.status_code in {401, 403}:
                    return ProviderDiscoveryResult(
                        provider=self.provider,
                        query=request.query,
                        ok=False,
                        results=[],
                        raw=None,
                        error=ProviderDiscoveryError(
                            code="auth_error",
                            message="Serper authentication failed.",
                            details=_safe_text(resp),
                        ),
                    )

                # Retryable conditions: 429 + transient server errors.
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    last_err = _safe_text(resp)
                    if attempt < self._max_retries:
                        await self._backoff(resp, attempt=attempt)
                        continue

                # Non-retryable client errors, or exhausted retries.
                if resp.status_code == 429:
                    return ProviderDiscoveryResult(
                        provider=self.provider,
                        query=request.query,
                        ok=False,
                        results=[],
                        raw=None,
                        error=ProviderDiscoveryError(
                            code="rate_limited",
                            message="Serper rate limit exceeded.",
                            details=_safe_text(resp),
                        ),
                    )
                return ProviderDiscoveryResult(
                    provider=self.provider,
                    query=request.query,
                    ok=False,
                    results=[],
                    raw=None,
                    error=ProviderDiscoveryError(
                        code="provider_error",
                        message=f"Serper request failed (status={resp.status_code}).",
                        details=_safe_text(resp),
                    ),
                )
            except (httpx.TimeoutException, httpx.HTTPError) as e:
                last_err = str(e)
                if attempt < self._max_retries:
                    await asyncio.sleep(min(8.0, 0.5 * (2**attempt)) + random.random() * 0.25)
                    continue
                return ProviderDiscoveryResult(
                    provider=self.provider,
                    query=request.query,
                    ok=False,
                    results=[],
                    raw=None,
                    error=ProviderDiscoveryError(code="http_error", message="HTTP request failed", details=str(e)),
                )

        return ProviderDiscoveryResult(
            provider=self.provider,
            query=request.query,
            ok=False,
            results=[],
            raw=None,
            error=ProviderDiscoveryError(code="provider_error", message="Serper request failed", details=last_err),
        )

    async def _throttle(self) -> None:
        if self._min_interval_seconds <= 0:
            return
        async with self._rate_lock:
            now = time.monotonic()
            wait = self._min_interval_seconds - (now - self._last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    async def _backoff(self, resp: httpx.Response, *, attempt: int) -> None:
        retry_after = resp.headers.get("retry-after")
        if retry_after:
            try:
                seconds = float(retry_after)
                await asyncio.sleep(min(60.0, max(0.0, seconds)))
                return
            except ValueError:
                pass
        # Exponential backoff with small jitter.
        await asyncio.sleep(min(30.0, 1.0 * (2**attempt)) + random.random() * 0.25)

    @staticmethod
    def _normalize_results(body: dict[str, Any], *, preferred_bucket: str) -> list[ProviderSearchResult]:
        # Prefer the bucket matching the endpoint (eg `shopping`), but fall back to `organic`.
        buckets: list[tuple[str, Any]] = []
        if preferred_bucket in body:
            buckets.append((preferred_bucket, body.get(preferred_bucket)))
        if "organic" in body and preferred_bucket != "organic":
            buckets.append(("organic", body.get("organic")))

        # As a final fallback, scan known buckets in stable order.
        if not buckets:
            for key in ("shopping", "images", "news", "places", "videos", "organic"):
                if key in body:
                    buckets.append((key, body.get(key)))

        out: list[ProviderSearchResult] = []
        for bucket_name, items in buckets:
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                url = item.get("link") or item.get("website")
                if not url:
                    continue
                out.append(
                    ProviderSearchResult(
                        title=item.get("title"),
                        url=str(url),
                        snippet=item.get("snippet") or item.get("description"),
                        source=item.get("source") or item.get("domain"),
                        rank=item.get("position"),
                        type=bucket_name,
                        extra={
                            k: v
                            for k, v in item.items()
                            if k
                            not in {
                                "title",
                                "link",
                                "website",
                                "snippet",
                                "description",
                                "source",
                                "domain",
                                "position",
                            }
                        },
                    )
                )
        return out


def _safe_text(resp: httpx.Response) -> str:
    # Avoid returning huge bodies.
    try:
        txt = resp.text or ""
    except Exception:
        return ""
    return txt[:2000]

