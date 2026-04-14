"""Фикстуры pytest."""

import pytest

from gateway.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()


@pytest.fixture
def test_api_key() -> str:
    return "test-api-key-for-ci"


@pytest.fixture(autouse=True)
def env_api_key(test_api_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GATEWAY_API_KEYS", test_api_key)
    get_settings.cache_clear()
