"""Provider discovery service: routes requests to provider services."""

from __future__ import annotations

import asyncio

from vibeify_api.clients.registry import default_provider_services
from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import ProviderDiscoveryError, ProviderDiscoveryRequest
from vibeify_api.schemas.responses import ProviderDiscoveryResponse, ProviderDiscoveryResult


class DiscoveryService:
    """Orchestrates provider discovery: resolves provider name to service, calls service.search(request)."""

    def __init__(
        self,
        *,
        services: dict[str, object] | None = None,
    ) -> None:
        self._logger = get_logger(self.__class__.__name__)
        self._services = services or default_provider_services()

    async def discover(self, requests: list[ProviderDiscoveryRequest]) -> ProviderDiscoveryResponse:
        """Process discovery requests (one per provider service) and return standardized results."""
        coros = [self._discover_one(req) for req in requests]
        results = await asyncio.gather(*coros)
        return ProviderDiscoveryResponse(results=results)

    async def _discover_one(self, request: ProviderDiscoveryRequest) -> ProviderDiscoveryResult:
        provider = (request.provider or "").lower().strip()
        service = self._services.get(provider)
        if service is None:
            return ProviderDiscoveryResult(
                provider=provider or request.provider,
                results=[],
                error=ProviderDiscoveryError(
                    code="unknown_provider",
                    message=f"Unsupported provider '{provider}'",
                ),
            )
        try:
            return await service.search(request)
        except Exception as e:
            self._logger.exception("Provider discovery failed", extra={"provider": provider})
            return ProviderDiscoveryResult(
                provider=provider,
                results=[],
                error=ProviderDiscoveryError(code="provider_failed", message="Provider call failed", details=str(e)),
            )

