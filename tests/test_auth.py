"""Проверка X-Api-Key middleware."""

import pytest
from fastapi.testclient import TestClient

from gateway.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_without_key(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_orders_without_key(client: TestClient) -> None:
    r = client.post("/api/v1/orders", json={})
    assert r.status_code == 401


def test_orders_with_bad_key(client: TestClient) -> None:
    r = client.post(
        "/api/v1/orders",
        json={},
        headers={"X-Api-Key": "wrong"},
    )
    assert r.status_code == 401


def test_openapi_public(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
