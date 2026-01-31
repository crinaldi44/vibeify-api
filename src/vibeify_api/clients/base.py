from __future__ import annotations

from typing import Any

from vibeify_api.core.logging import get_logger
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest
from vibeify_api.services.http_client import HttpClientService


class ProviderClient[T]:

    def __init__(self):
        self._logger = get_logger(self.__class__.__name__)

    provider: str

    async def search(self, request: ProviderDiscoveryRequest, http: HttpClientService) -> T:
        raise NotImplementedError("Method not implemented.")

    def _standard_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "vibeify-api-discovery/0.1 (+https://vibeify)",
            "Accept": "*/*",
        }
