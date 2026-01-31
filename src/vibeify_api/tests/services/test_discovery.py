import httpx
import pytest

from vibeify_api.clients.registry import default_provider_clients
from vibeify_api.clients.serper import SerperClient
from vibeify_api.schemas.discovery import ProviderDiscoveryRequest
from vibeify_api.services.discovery import DiscoveryService


class _StubHttp:
    def __init__(self, responses: list[httpx.Response]):
        self._responses = list(responses)

    async def request(  # matches HttpClientService.request signature well enough for tests
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


@pytest.mark.asyncio
async def test_serper_missing_api_key_returns_error():
    client = SerperClient(api_key=None)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    resp = await client.search(req, http=_StubHttp([]))  # http not used when missing key
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error.code == "missing_api_key"


@pytest.mark.asyncio
async def test_serper_normalizes_organic_results():
    client = SerperClient(api_key="test")
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search", includeRaw=True)

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
    http = _StubHttp([httpx.Response(200, json=body)])
    resp = await client.search(req, http=http)

    assert resp.ok is True
    assert resp.raw is not None
    assert len(resp.results) == 1
    r0 = resp.results[0]
    assert r0.url == "https://www.lego.com/"
    assert r0.title == "LEGO"
    assert r0.rank == 1
    assert r0.result_type == "organic"
    assert "sitelinks" in r0.extra


@pytest.mark.asyncio
async def test_serper_429_returns_rate_limited_code():
    client = SerperClient(api_key="test", max_retries=0)
    req = ProviderDiscoveryRequest(provider="serper", query="lego", type="search")
    http = _StubHttp([httpx.Response(429, json={"message": "rate limit"})])
    resp = await client.search(req, http=http)
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error.code == "rate_limited"


def test_default_provider_registry_contains_serper():
    reg = default_provider_clients()
    assert "serper" in reg
    assert "amazon" in reg


@pytest.mark.asyncio
async def test_discovery_service_unknown_provider():
    svc = DiscoveryService(clients={})
    resp = await svc.discover([ProviderDiscoveryRequest(provider="nope", query="x")])
    assert len(resp.results) == 1
    r0 = resp.results[0]
    assert r0.ok is False
    assert r0.error is not None
    assert r0.error.code == "unknown_provider"

