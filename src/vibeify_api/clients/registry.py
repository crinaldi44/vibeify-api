"""Provider client registry utilities."""

from __future__ import annotations

from typing import Any

from vibeify_api.clients.base import ProviderClient
from vibeify_api.clients.serper import SerperClient


def default_provider_clients() -> dict[str, ProviderClient[Any]]:
    """Default provider clients enabled in this service."""
    return {
        SerperClient.provider: SerperClient(),
    }

