"""
E2E против реального стенда (создаёт заказ в Bitrix).

Запуск: GATEWAY_E2E=1 pytest -q tests/test_e2e_staging.py
Переменные: GATEWAY_BITRIX_BASE_URL, GATEWAY_BITRIX_VERIFY_TLS, BITRIX_STAGING_PRODUCT_ID
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import pytest

from gateway.bitrix_client import BitrixClient
from gateway.config import Settings
from gateway.mappers import order_request_to_form_fields
from gateway.schemas import OrderRequest

pytestmark = pytest.mark.skipif(
    os.environ.get("GATEWAY_E2E") != "1",
    reason="Set GATEWAY_E2E=1 to run staging E2E",
)


@pytest.fixture
def e2e_settings() -> Settings:
    base = os.environ.get("GATEWAY_BITRIX_BASE_URL", "https://ai-test.buketopt.ru")
    env_flag = os.environ.get("GATEWAY_BITRIX_VERIFY_TLS", "false").lower()
    simple = os.environ.get("GATEWAY_USE_SIMPLE_ORDER", "false").lower()
    return Settings(
        api_keys="e2e-unused",
        bitrix_base_url=base,  # type: ignore[arg-type]
        bitrix_verify_tls=env_flag in ("1", "true", "yes"),
        default_payment_method_id=int(os.environ.get("GATEWAY_DEFAULT_PAYMENT_METHOD_ID", "15")),
        use_simple_order=simple in ("1", "true", "yes"),
    )


async def _prefetch_pickup_time(
    hc: httpx.AsyncClient,
    form_base: dict[str, Any],
) -> tuple[str, int]:
    """Через checkout получить первый активный интервал и VALUE магазина (тот же клиент/cookie)."""
    r = await hc.post("/local/rest/front/order/checkout/", data=form_base)
    r.raise_for_status()
    payload: dict[str, Any] = r.json()
    data = payload.get("data")
    if not isinstance(data, dict):
        return "0", 1
    tr = data.get("time_ranges") or []
    tcode = "0"
    if isinstance(tr, list):
        for row in tr:
            if isinstance(row, dict) and row.get("active") == 1:
                tcode = str(row.get("value", "0"))
                break
    shops = data.get("pickup_shops_data") or []
    shop_val = 1
    if isinstance(shops, list) and shops:
        first = shops[0]
        if isinstance(first, dict) and first.get("VALUE") is not None:
            shop_val = int(str(first["VALUE"]))
    return tcode, shop_val


@pytest.mark.asyncio
async def test_gateway_chain_real_bitrix(e2e_settings: Settings) -> None:
    """Цепочка session → basket → checkout → create (реальный Bitrix)."""
    pid = int(os.environ.get("BITRIX_STAGING_PRODUCT_ID", "296"))
    req = OrderRequest(
        product_id=pid,
        quantity=1,
        customer_name="E2E Gateway",
        customer_phone="+79001112233",
        customer_email="e2e-gateway@test.invalid",
        recipient_name="E2E Recipient",
        recipient_phone="+79004445566",
        delivery_date="20.04.2026",
        delivery_type="pickup",
        address="",
        payment_method_id=15,
        comment="e2e buketopt-gateway",
        source="site",
        time_range="default",
        pickup_shop_val=1,
    )
    form_partial = order_request_to_form_fields(req, e2e_settings)
    client = BitrixClient(e2e_settings)
    async with client._client() as hc:  # noqa: SLF001
        session = await client.fetch_session_id(hc)
        form_partial["session"] = session
        await client.add_to_basket(hc, session, pid, 1)
        tcode, shop_val = await _prefetch_pickup_time(hc, form_partial)
        req2 = req.model_copy(update={"time_range": tcode, "pickup_shop_val": shop_val})
        form = order_request_to_form_fields(req2, e2e_settings)
        form["session"] = session
        await client.order_checkout(hc, form)
        result = await client.order_create(hc, form)

    if result.status == "created":
        assert result.order_id is not None
        assert result.payment_link is None or result.payment_link.startswith("http")
        return

    msg = " ".join(result.errors)
    if "curl_init" in msg or "fatal-error" in msg:
        pytest.skip(f"инфраструктура стенда (PHP/curl): {msg}")
    pytest.fail(f"ожидался created: {result.errors}")


@pytest.mark.asyncio
async def test_session_get_only(e2e_settings: Settings) -> None:
    """Минимальная проверка TLS/маршрута."""
    c = BitrixClient(e2e_settings)
    async with c._client() as hc:  # noqa: SLF001
        sid = await c.fetch_session_id(hc)
    assert len(sid) >= 8
