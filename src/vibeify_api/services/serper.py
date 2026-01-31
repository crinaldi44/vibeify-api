"""Serper provider service: normalization and error mapping. Uses SerperClient for HTTP (client owns retries)."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import (
    ProviderDiscoveryError,
    ProviderDiscoveryRequest,
    ProviderSearchResult,
)
from vibeify_api.schemas.responses import ProviderDiscoveryResult


def _safe_text(resp: httpx.Response) -> str:
    try:
        txt = resp.text or ""
    except Exception:
        return ""
    return txt[:2000]


def _normalize_serper_results(body: dict[str, Any], *, preferred_bucket: str) -> list[ProviderSearchResult]:
    buckets: list[tuple[str, Any]] = []
    if preferred_bucket in body:
        buckets.append((preferred_bucket, body.get(preferred_bucket)))
    if "organic" in body and preferred_bucket != "organic":
        buckets.append(("organic", body.get("organic")))
    if not buckets:
        for key in ("shopping", "images", "news", "places", "videos", "organic"):
            if key in body:
                buckets.append((key, body.get(key)))
                break

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


class SerperService:
    """Provider service for Serper: normalization and error mapping. Client owns retries."""

    def __init__(self) -> None:
        self._client = SerperClient()

    async def search(self, request: ProviderDiscoveryRequest) -> ProviderDiscoveryResult:
        """Call Serper (client retries), normalize response, return ProviderDiscoveryResult."""

        search_type = (request.search_type or "search").strip().lower()
        endpoint = search_type if search_type else "search"

        async with self._client as client:
            try:
                resp = await client.fetch(request)
            except ValueError as e:
                if "API key" in str(e):
                    return ProviderDiscoveryResult(
                        provider=self._client.provider,
                        results=[],
                        error=ProviderDiscoveryError(code="missing_api_key", message=str(e)),
                    )
                raise
            except httpx.TimeoutException as e:
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=[],
                    error=ProviderDiscoveryError(
                        code="timeout",
                        message="Request timed out",
                        details=str(e),
                    ),
                )
            except httpx.HTTPError as e:
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=[],
                    error=ProviderDiscoveryError(
                        code="http_error",
                        message="HTTP request failed",
                        details=str(e),
                    ),
                )

            if 200 <= resp.status_code < 300:
                body = resp.json()
                results = _normalize_serper_results(body, preferred_bucket=endpoint)
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=results,
                    error=None,
                )

            if resp.status_code in (401, 403):
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=[],
                    error=ProviderDiscoveryError(
                        code="auth_error",
                        message="Serper authentication failed.",
                        details=_safe_text(resp),
                    ),
                )

            if resp.status_code == 429:
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=[],
                    error=ProviderDiscoveryError(
                        code="rate_limited",
                        message="Serper rate limit exceeded.",
                        details=_safe_text(resp),
                    ),
                )

            if 500 <= resp.status_code < 600:
                return ProviderDiscoveryResult(
                    provider=self._client.provider,
                    results=[],
                    error=ProviderDiscoveryError(
                        code="provider_error",
                        message=f"Serper request failed (status={resp.status_code}).",
                        details=_safe_text(resp),
                    ),
                )

            return ProviderDiscoveryResult(
                provider=self._client.provider,
                results=[],
                error=ProviderDiscoveryError(
                    code="provider_error",
                    message=f"Serper request failed (status={resp.status_code}).",
                    details=_safe_text(resp),
                ),
            )
