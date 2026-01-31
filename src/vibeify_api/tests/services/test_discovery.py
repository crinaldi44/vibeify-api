"""Tests for provider discovery: thin client (repository), SerperService, DiscoveryService."""

import httpx
import pytest

from vibeify_api.clients.registry import default_provider_services
from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest
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
async def test_serper_client_fetch_raises_when_no_api_key():
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    async with SerperClient(api_key=None) as client:
        with pytest.raises(ValueError, match="API key"):
            await client.fetch(req)


@pytest.mark.asyncio
async def test_serper_client_fetch_returns_raw_response():
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    body = {"organic": [{"title": "LEGO", "link": "https://www.lego.com/", "position": 1}]}
    stub_http = _StubHttp([httpx.Response(200, json=body)])
    client = SerperClient(api_key="test", _http=stub_http)
    async with client as c:
        resp = await c.fetch(req)
    assert resp.status_code == 200
    assert resp.json() == body


@pytest.mark.asyncio
async def test_serper_client_retries_on_429_then_returns_success():
    """Client retries on 429 and returns the final 200 response."""
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    body = {"organic": [{"title": "LEGO", "link": "https://www.lego.com/", "position": 1}]}
    stub_http = _StubHttp([
        httpx.Response(429, json={"message": "rate limit"}),
        httpx.Response(200, json=body),
    ])
    client = SerperClient(api_key="test", _http=stub_http)
    async with client as c:
        resp = await c.fetch(req)
    assert resp.status_code == 200
    assert resp.json() == body


@pytest.mark.asyncio
async def test_serper_client_fetch_raw_matches_fetch_for_same_request():
    """fetch_raw with equivalent url+payload returns same response as fetch(request)."""
    body = {"organic": [{"title": "LEGO", "link": "https://www.lego.com/", "position": 1}]}
    recording_stub = _RecordingStubHttp([
        httpx.Response(200, json=body),
        httpx.Response(200, json=body),
    ])
    client = SerperClient(api_key="test", base_url="https://google.serper.dev", _http=recording_stub)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search", num=10)

    async with client as c:
        resp_fetch = await c.fetch(req)

    url = "https://google.serper.dev/search"
    payload = {"q": "lego", "num": 10}
    async with SerperClient(api_key="test", base_url="https://google.serper.dev", _http=recording_stub) as c:
        resp_raw = await c.execute_request("POST", url, json=payload)

    assert resp_fetch.status_code == 200
    assert resp_raw.status_code == 200
    assert resp_fetch.json() == resp_raw.json() == body
    assert recording_stub.last_url == url
    assert recording_stub.last_json == payload


@pytest.mark.asyncio
async def test_serper_client_fetch_raw_raises_when_no_api_key():
    """fetch_raw raises ValueError when API key is not configured."""
    client = SerperClient(api_key=None)
    async with client as c:
        with pytest.raises(ValueError, match="API key"):
            await c.execute_request("POST", "https://google.serper.dev/search", json={"q": "lego"})


# ---- SerperService tests (stub client returns fixed response) ----
class _StubSerperClient:
    provider = "serper"
    _api_key = "stub"

    def __init__(self, responses: list[httpx.Response]):
        self._responses = list(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def fetch(self, request):
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
    assert r0.url == "https://www.lego.com/"
    assert r0.title == "LEGO"
    assert r0.rank == 1
    assert r0.result_type == "organic"
    assert "sitelinks" in r0.extra


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
    resp = await svc.discover([ProviderDiscoveryRequest(provider="nope", query="x")])
    assert len(resp.results) == 1
    r0 = resp.results[0]
    assert r0.error is not None
    assert r0.error.code == "unknown_provider"
