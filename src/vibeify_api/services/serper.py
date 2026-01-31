"""Serper provider service: success normalization only. BaseDiscoveryService handles errors."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest, ProviderSearchResult
from vibeify_api.schemas.responses import ProviderDiscoveryResult
from vibeify_api.services.base import BaseDiscoveryService

class SerperService(BaseDiscoveryService):
    """Provider service for Serper: normalizes 2xx responses. Base handles errors."""

    def __init__(self, *, client: Optional[SerperClient] = None) -> None:
        super().__init__(client=client or SerperClient())

    @staticmethod
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

    async def _normalize_success(
        self,
        resp: httpx.Response,
        request: ProviderDiscoveryRequest,
    ) -> ProviderDiscoveryResult:
        body = resp.json()
        endpoint = (request.search_type or "search").strip().lower() or "search"
        results = self._normalize_serper_results(body, preferred_bucket=endpoint)
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=results,
            error=None,
        )
