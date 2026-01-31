"""Provider discovery service: routes requests to provider clients concurrently."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from vibeify_api.clients.registry import default_provider_clients
from vibeify_api.clients.base import ProviderClient
from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import ProviderDiscoveryError, ProviderDiscoveryRequest
from vibeify_api.schemas.responses import ProviderDiscoveryResponse, ProviderDiscoveryResult
from vibeify_api.services.http_client import HttpClientService


class DiscoveryService:
    """Orchestrates provider discovery across providers with standardized results."""

    def __init__(
        self,
        *,
        clients: dict[str, ProviderClient[Any]] | None = None,
        max_concurrency: int = 10,
    ) -> None:
        self._logger = get_logger(self.__class__.__name__)
        self._clients: dict[str, ProviderClient[Any]] = clients or default_provider_clients()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def discover(self, requests: list[ProviderDiscoveryRequest]) -> ProviderDiscoveryResponse:
        """Concurrently process discovery requests and return standardized results."""
        async with HttpClientService() as http:
            coros = [self._discover_one(req, http=http) for req in requests]
            results = await asyncio.gather(*coros)
        return ProviderDiscoveryResponse(results=results)

    async def _discover_one(
        self,
        request: ProviderDiscoveryRequest,
        *,
        http: HttpClientService,
    ) -> ProviderDiscoveryResult:
        provider = (request.provider or "").lower().strip()
        client = self._clients.get(provider)
        if client is None:
            return ProviderDiscoveryResult(
                provider=provider or request.provider,
                query=request.query,
                ok=False,
                results=[],
                raw=None,
                error=ProviderDiscoveryError(
                    code="unknown_provider",
                    message=f"Unsupported provider '{provider}'",
                ),
            )

        async with self._semaphore:
            try:
                return await client.search(request, http=http)
            except httpx.TimeoutException as e:
                self._logger.warning("Provider discovery timeout", extra={"provider": provider})
                return ProviderDiscoveryResult(
                    provider=provider,
                    query=request.query,
                    ok=False,
                    results=[],
                    raw=None,
                    error=ProviderDiscoveryError(code="timeout", message="Provider request timed out", details=str(e)),
                )
            except httpx.HTTPError as e:
                self._logger.warning("Provider discovery HTTP error", extra={"provider": provider})
                return ProviderDiscoveryResult(
                    provider=provider,
                    query=request.query,
                    ok=False,
                    results=[],
                    raw=None,
                    error=ProviderDiscoveryError(code="http_error", message="HTTP request failed", details=str(e)),
                )
            except Exception as e:
                self._logger.exception("Provider discovery failed", extra={"provider": provider})
                return ProviderDiscoveryResult(
                    provider=provider,
                    query=request.query,
                    ok=False,
                    results=[],
                    raw=None,
                    error=ProviderDiscoveryError(code="provider_failed", message="Provider call failed", details=str(e)),
                )

