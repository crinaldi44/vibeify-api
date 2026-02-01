"""Tests for provider discovery: thin client (repository), SerperService, DiscoveryService."""

import httpx
import pytest

from vibeify_api.clients.registry import default_provider_services
from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest, ProductOfferDiscoveryResult
from vibeify_api.services.discovery import DiscoveryService
from vibeify_api.services.serper import SerperService


class _StubHttp:
    def __init__(self, responses: list[httpx.Response]):
        self._responses = list(responses)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        headers=None,
        json=None,
        data=None,
    ) -> httpx.Response:
        assert self._responses, "No more stubbed responses"
        return self._responses.pop(0)


class _RecordingStubHttp(_StubHttp):
    """Stub that records the last request for assertion."""

    def __init__(self, responses: list[httpx.Response]):
        super().__init__(responses)
        self.last_method: str | None = None
        self.last_url: str | None = None
        self.last_json: dict | None = None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        headers=None,
        json=None,
        data=None,
    ) -> httpx.Response:
        self.last_method = method
        self.last_url = url
        self.last_json = json
        return await super().request(method, url, params=params, headers=headers, json=json, data=data)


# ---- Thin client (repository) tests ----
@pytest.mark.asyncio
async def test_serper_client_execute_request_raises_when_no_api_key():
    async with SerperClient(api_key=None) as client:
        with pytest.raises(ValueError, match="API key"):
            await client.execute_request("POST", "https://google.serper.dev/search", json={"q": "lego"})


@pytest.mark.asyncio
async def test_serper_client_execute_request_returns_raw_response():
    body = {"organic": [{"title": "LEGO", "link": "https://www.lego.com/", "position": 1}]}
    stub_http = _StubHttp([httpx.Response(200, json=body)])
    client = SerperClient(api_key="test", _http=stub_http)
    async with client as c:
        resp = await c.execute_request("POST", "https://google.serper.dev/search", json={"q": "lego"})
    assert resp.status_code == 200
    assert resp.json() == body


@pytest.mark.asyncio
async def test_serper_client_retries_on_429_then_returns_success():
    """Client retries on 429 and returns the final 200 response."""
    body = {"organic": [{"title": "LEGO", "link": "https://www.lego.com/", "position": 1}]}
    stub_http = _StubHttp([
        httpx.Response(429, json={"message": "rate limit"}),
        httpx.Response(200, json=body),
    ])
    client = SerperClient(api_key="test", _http=stub_http)
    async with client as c:
        resp = await c.execute_request("POST", "https://google.serper.dev/search", json={"q": "lego"})
    assert resp.status_code == 200
    assert resp.json() == body


@pytest.mark.asyncio
async def test_serper_client_execute_request_sends_correct_url_and_payload():
    """execute_request sends correct URL and JSON payload."""
    body = {"organic": [{"link": "https://example.com/"}]}
    recording_stub = _RecordingStubHttp([httpx.Response(200, json=body)])
    client = SerperClient(api_key="test", base_url="https://google.serper.dev", _http=recording_stub)
    url = "https://google.serper.dev/search"
    payload = {"q": "lego", "engine": "ebay_product"}
    async with client as c:
        resp = await c.execute_request("POST", url, json=payload)
    assert resp.status_code == 200
    assert recording_stub.last_url == url
    assert recording_stub.last_json == payload


# ---- SerperService tests (stub client returns fixed response) ----
class _StubSerperClient:
    provider = "serper"
    _api_key = "stub"
    _base_url = "https://google.serper.dev"

    def __init__(self, responses: list[httpx.Response]):
        self._responses = list(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def execute_request(self, method: str, url: str, *, json: dict | None = None, **kwargs):
        assert self._responses, "No more stubbed responses"
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_serper_service_missing_api_key_returns_error():
    service = SerperService(client=SerperClient(api_key=None))
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    result = await service.search(req)
    assert result.error is not None
    assert result.error.code == "missing_api_key"


@pytest.mark.asyncio
async def test_serper_service_normalizes_organic_results():
    """SerperService returns ProviderDiscoveryResult[SerperSearchResult] with url from organic items."""
    body = {
        "organic": [
            {
                "title": "LEGO",
                "link": "https://www.lego.com/",
                "snippet": "Official LEGO site",
                "position": 1,
                "sitelinks": [{"title": "Shop", "link": "https://www.lego.com/en-us"}],
            }
        ]
    }
    stub = _StubSerperClient([httpx.Response(200, json=body)])
    service = SerperService(client=stub)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    result = await service.search(req)
    assert result.error is None
    assert len(result.results) == 1
    r0 = result.results[0]
    assert isinstance(r0, ProductOfferDiscoveryResult)
    assert r0.url == "https://www.lego.com/"


@pytest.mark.asyncio
async def test_serper_service_429_returns_rate_limited_code():
    stub = _StubSerperClient([httpx.Response(429, json={"message": "rate limit"})])
    service = SerperService(client=stub)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    result = await service.search(req)
    assert result.error is not None
    assert result.error.code == "rate_limited"


@pytest.mark.asyncio
async def test_serper_service_401_returns_auth_error():
    """_execute_fetch returns ProviderDiscoveryResult with auth_error for 401."""
    stub = _StubSerperClient([httpx.Response(401, json={"message": "Unauthorized"})])
    service = SerperService(client=stub)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    result = await service.search(req)
    assert result.error is not None
    assert result.error.code == "auth_error"


def test_default_provider_services_contains_serper():
    reg = default_provider_services()
    assert "serper" in reg


@pytest.mark.asyncio
async def test_discovery_service_unknown_provider():
    svc = DiscoveryService(services={})
    resp = await svc.discover_offers([ProviderDiscoveryRequest(provider="nope", query="x")])
    assert len(resp.results) == 1
    r0 = resp.results[0]
    assert r0.error is not None
    assert r0.error.code == "unknown_provider"
