"""Мок цепочки Bitrix → POST /api/v1/orders."""

import json
from typing import Any

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from gateway.app import app
from gateway.config import Settings, get_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"status": True, "error": {}, "data": data}


def test_create_order_success(client: TestClient, test_api_key: str) -> None:
    base = "https://ai-test.buketopt.example"

    with respx.mock(assert_all_called=False) as router:
        router.post(f"{base}/local/rest/front/session/get/").mock(
            return_value=httpx.Response(200, json=_ok({"session": "sess-abc"})),
        )
        router.post(f"{base}/local/rest/front/basket/add/").mock(
            return_value=httpx.Response(200, json=_ok({})),
        )
        router.post(f"{base}/local/rest/front/order/checkout/").mock(
            return_value=httpx.Response(200, json=_ok({})),
        )
        router.post(f"{base}/local/rest/front/order/create/").mock(
            return_value=httpx.Response(
                200,
                json=_ok({"order_id": 4242, "payment_link": "https://pay.example/4242"}),
            ),
        )

        def _settings() -> Settings:
            return Settings(
                api_keys=test_api_key,
                bitrix_base_url=base,  # type: ignore[arg-type]
            )

        app.dependency_overrides[get_settings] = _settings
        try:
            body = {
                "product_id": 296,
                "quantity": 1,
                "customer_name": "Иван",
                "customer_phone": "+79001234567",
                "recipient_name": "Мария",
                "recipient_phone": "+79007654321",
                "delivery_date": "15.04.2026",
                "delivery_type": "courier",
                "address": "Москва, ул. Тестовая, 1",
                "payment_method_id": 15,
            }
            r = client.post(
                "/api/v1/orders",
                json=body,
                headers={"X-Api-Key": test_api_key},
            )
        finally:
            app.dependency_overrides.clear()
            get_settings.cache_clear()

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    assert data["order_id"] == 4242
    assert data["payment_link"] == "https://pay.example/4242"


def test_create_order_bitrix_error(client: TestClient, test_api_key: str) -> None:
    base = "https://example-bitrix.test"

    with respx.mock(assert_all_called=False) as router:
        router.post(f"{base}/local/rest/front/session/get/").mock(
            return_value=httpx.Response(200, json=_ok({"session": "s1"})),
        )
        router.post(f"{base}/local/rest/front/basket/add/").mock(
            return_value=httpx.Response(
                200,
                json={"status": False, "error": {"code": "basket"}, "data": {}},
            ),
        )

        def _settings() -> Settings:
            return Settings(
                api_keys=test_api_key,
                bitrix_base_url=base,  # type: ignore[arg-type]
            )

        app.dependency_overrides[get_settings] = _settings
        try:
            body = {
                "product_id": 1,
                "quantity": 1,
                "customer_name": "A",
                "customer_phone": "+70000000000",
                "recipient_name": "B",
                "recipient_phone": "+70000000001",
                "delivery_date": "01.01.2026",
            }
            r = client.post(
                "/api/v1/orders",
                json=body,
                headers={"X-Api-Key": test_api_key},
            )
        finally:
            app.dependency_overrides.clear()
            get_settings.cache_clear()

    assert r.status_code == 200
    assert r.json()["status"] == "error"
    assert r.json()["errors"]


def test_create_order_empty_body(client: TestClient, test_api_key: str) -> None:
    r = client.post(
        "/api/v1/orders",
        content=json.dumps({}),
        headers={"X-Api-Key": test_api_key, "Content-Type": "application/json"},
    )
    assert r.status_code == 422


def test_api_no_keys_configured(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("GATEWAY_API_KEYS", "")
    get_settings.cache_clear()
    r = client.post(
        "/api/v1/orders",
        json={},
        headers={"X-Api-Key": "x"},
    )
    assert r.status_code == 503
