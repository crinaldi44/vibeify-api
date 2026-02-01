"""Serper provider service: success normalization only. BaseDiscoveryService handles errors."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest, ProductRecord, ProviderDiscoveryResult, \
    ProductIdentifierRecord, ProductSpecificationRecord, BrandRecord
from vibeify_api.schemas.enums import ProductIdentifierType
from vibeify_api.schemas.serper import SerperEbayProductResponse
from vibeify_api.services.base import BaseDiscoveryService


class SerperService(BaseDiscoveryService):
    """Provider service for Serper."""

    ebay_engine_path = "/search?engine=ebay_product"

    def __init__(self, *, client: Optional[SerperClient] = None):
        super().__init__(client=client or SerperClient())

    async def _normalize_product_results(self, resp: httpx.Response) -> ProviderDiscoveryResult[ProductRecord]:
        """Normalize serper product search results."""
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=[],
        )

    async def _extract_product_specification_groups(self, external_result: SerperEbayProductResponse) -> tuple[list[ProductIdentifierRecord], str | None, list[ProductSpecificationRecord]]:
        """ Extract product identifiers, brand name, and specification records from the "About This Item" section.

        :param external_result:
        :return:
        """
        identifier_records: list[ProductIdentifierRecord] = []
        product_specification_records: list[ProductSpecificationRecord] = []
        brand: str | None = None
        for _group in external_result.product_results.specifications.groups:
            if _group.type == "about_this_item":
                for _section in _group.sections:
                    for _field in _section.fields:
                        if _field.type == "brand":
                            brand = _field.value
                        pass
        return identifier_records, brand, product_specification_records

    async def _extract_source_category_paths(self, external_result: SerperEbayProductResponse) -> list[str]:
        """ Extract source category paths from the response.

        :param external_result:
        :return:
        """
        return list(map(lambda x: x.title, external_result.product_results.categories))

    async def _normalize_product_details(self, resp: httpx.Response) -> ProviderDiscoveryResult[ProductRecord]:
        """Normalize serper product details."""
        ebay_response = SerperEbayProductResponse.model_validate(resp.json())
        external_result = ebay_response.product_results

        identifier_records, brand, product_specification_records = await self._extract_product_specification_groups(ebay_response)
        source_category_paths = await self._extract_source_category_paths(ebay_response)

        brand = BrandRecord(
            name=brand
        )

        product_result = ProductRecord(
            name=external_result.title,
            description=external_result.short_description,
            brand_record=brand,
            source_product_url=external_result.product_link,
            product_identifier_records=identifier_records,
            source_category_paths=source_category_paths,
            data_source=self._client.provider
        )
        return ProviderDiscoveryResult(
            provider=self._client.provider,
            results=[
                product_result
            ],
        )

    async def offer_enrichment(
        self, request: ProviderDiscoveryRequest
    ) -> ProviderDiscoveryResult[ProductRecord]:
        """Provide enriched offer details using the offer ID from the provider."""
        url = f"{self._client._base_url.rstrip('/')}/offer"
        return await self._execute_fetch(
            lambda: self._client.execute_request("GET", url),
            lambda resp: self._normalize_product_details(resp),
        )

    async def offer_search(
        self, request: ProviderDiscoveryRequest
    ) -> ProviderDiscoveryResult[ProductRecord]:
        """Perform a broad offer search to the provider and normalize the results."""
        url = f"{self._client._base_url.rstrip('/')}/search"
        payload = {"q": request.query, "engine": "ebay_product"}
        return await self._execute_fetch(
            lambda: self._client.execute_request("POST", url, json=payload),
            lambda resp: self._normalize_product_results(resp),
        )
