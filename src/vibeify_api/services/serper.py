"""Serper provider service: success normalization only. BaseDiscoveryService handles errors."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest, ProviderSearchResult
from vibeify_api.schemas.responses import ProviderDiscoveryResult
from vibeify_api.schemas.serper import SerperEbayProductResponse
from vibeify_api.services.base import BaseDiscoveryService

class SerperService(BaseDiscoveryService):
    """Provider service for Serper."""

    ebay_engine_path = "/search?engine=ebay_product"

    def __init__(self):
        super().__init__(client=SerperClient())

    async def _normalize_product_results(self, resp: httpx.Response) -> ProviderDiscoveryResult:
        """ Normalize serper product search results.

        :param resp:
        :return:
        """
        # serper_product_result = SerperEbaySearchResponse.model_validate_json(resp.json())
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=[],
        )

    async def _normalize_product_details(self, resp: httpx.Response) -> ProviderDiscoveryResult:
        """ Normalize serper product details."""
        ebay_response = SerperEbayProductResponse.model_validate_json(resp.json())
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=[]
        )

    async def offer_enrichment(self, request: ProviderDiscoveryRequest) -> ProviderDiscoveryResult:
        """ Provides enriched offer details using the offer ID from the provider.

        :param request:
        :return:
        """
        result = await self._execute_fetch(
            lambda: self._client.execute_request("GET", "/offer"),
            lambda resp: resp.json()
        )
        return ProviderDiscoveryResult(provider=self._client.provider, results=[])

    async def offer_search(self, request: ProviderDiscoveryRequest) -> ProviderDiscoveryResult:
        """ Perform a broad offer search to the provider and normalize the results.

        :param request:
        :return:
        """
        result = await self._execute_fetch(
            lambda: self._client.execute_request("GET", "/search?engine=ebay_product"),
            lambda resp: self._normalize_product_results(resp),
        )
        return result
