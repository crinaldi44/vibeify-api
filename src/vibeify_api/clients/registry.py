"""Provider service registry: returns provider services (each holds its client)."""

from __future__ import annotations

from typing import Any, Protocol

from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest
from vibeify_api.schemas.responses import ProviderDiscoveryResult
from vibeify_api.services.serper import SerperService


class ProviderServiceProtocol(Protocol):
    async def search(self, request: ProviderDiscoveryRequest) -> ProviderDiscoveryResult: ...


def default_provider_services() -> dict[str, ProviderServiceProtocol]:
    return {
        SerperClient.provider: SerperService(client=SerperClient()),
    }

