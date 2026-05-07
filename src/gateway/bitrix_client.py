"""HTTP-клиент к `/local/rest/front/` с cookie-сессией."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from gateway.config import Settings
from gateway.mappers import merge_bitrix_errors
from gateway.schemas import OrderResponse

logger = logging.getLogger(__name__)


class BitrixRestError(RuntimeError):
    """Ошибка цепочки или ответа Bitrix."""


def _parse_json_safe(text: str) -> dict[str, Any]:
    import json

    try:
        raw: Any = json.loads(text)
    except json.JSONDecodeError as e:
        raise BitrixRestError(f"Invalid JSON from Bitrix: {e}") from e
    if not isinstance(raw, dict):
        raise BitrixRestError("Bitrix response is not a JSON object")
    return raw


class BitrixClient:
    """Один экземпляр = одна цепочка session → basket → checkout → create на одном AsyncClient."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = str(settings.bitrix_base_url).rstrip("/")
        self._timeout = httpx.Timeout(settings.bitrix_http_timeout_sec)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base,
            timeout=self._timeout,
            verify=self._settings.bitrix_verify_tls,
            follow_redirects=True,
        )

    async def fetch_session_id(self, client: httpx.AsyncClient) -> str:
        """POST session/get → data.session."""
        # allow_unauthorized помогает гостевому сценарию (как в order/create)
        r = await client.post(
            "/local/rest/front/session/get/",
            data={"allow_unauthorized": "1"},
        )
        r.raise_for_status()
        body = _parse_json_safe(r.text)
        if not body.get("status"):
            errs = merge_bitrix_errors(body)
            raise BitrixRestError("session/get failed: " + ("; ".join(errs) or r.text[:500]))
        data = body.get("data")
        if not isinstance(data, dict):
            raise BitrixRestError("session/get: missing data object")
        sess = data.get("session")
        if not isinstance(sess, str):
            raise BitrixRestError("session/get: missing data.session")
        if not sess:
            raise BitrixRestError("session/get: missing data.session")
        return sess

    async def add_to_basket(
        self,
        client: httpx.AsyncClient,
        session: str,
        product_id: int,
        quantity: int,
    ) -> None:
        r = await client.post(
            "/local/rest/front/basket/add/",
            data={
                "session": session,
                "product_id": str(product_id),
                "quantity": str(quantity),
            },
        )
        r.raise_for_status()
        body = _parse_json_safe(r.text)
        if not body.get("status"):
            errs = merge_bitrix_errors(body)
            raise BitrixRestError("basket/add failed: " + ("; ".join(errs) or r.text[:500]))

    async def order_checkout(self, client: httpx.AsyncClient, form: dict[str, Any]) -> None:
        r = await client.post("/local/rest/front/order/checkout/", data=form)
        r.raise_for_status()
        body = _parse_json_safe(r.text)
        if not body.get("status"):
            errs = merge_bitrix_errors(body)
            raise BitrixRestError("order/checkout failed: " + ("; ".join(errs) or r.text[:500]))

    async def order_create(self, client: httpx.AsyncClient, form: dict[str, Any]) -> OrderResponse:
        r = await client.post("/local/rest/front/order/create/", data=form)
        r.raise_for_status()
        body = _parse_json_safe(r.text)
        if not body.get("status"):
            errs = merge_bitrix_errors(body)
            return OrderResponse(status="error", errors=errs or ["order/create rejected"])
        data = body.get("data")
        if not isinstance(data, dict):
            return OrderResponse(status="error", errors=["order/create: missing data"])
        oid = data.get("order_id")
        if oid is None:
            return OrderResponse(
                status="error",
                errors=merge_bitrix_errors(body) or ["order_id missing"],
            )
        try:
            order_id = int(oid)
        except (TypeError, ValueError):
            return OrderResponse(status="error", errors=[f"invalid order_id: {oid!r}"])
        plink = data.get("payment_link")
        payment_link = str(plink) if plink else None
        return OrderResponse(
            order_id=order_id,
            payment_link=payment_link,
            status="created",
        )

    async def create_order_full_chain(
        self,
        product_id: int,
        quantity: int,
        form_fields: dict[str, Any],
    ) -> OrderResponse:
        """Полная цепочка на одном клиенте (cookie jar)."""
        async with self._client() as client:
            session = await self.fetch_session_id(client)
            form = {**form_fields, "session": session}
            await self.add_to_basket(client, session, product_id, quantity)
            await self.order_checkout(client, form)
            return await self.order_create(client, form)

    async def ping(self) -> tuple[bool, str | None]:
        """Лёгкая проверка доступности Bitrix (session/get)."""
        try:
            async with self._client() as client:
                await self.fetch_session_id(client)
            return True, None
        except Exception as e:
            logger.warning("Bitrix ping failed: %s", e)
            return False, str(e)

    async def get_order_card(self, order_id: int, session: str | None = None) -> dict[str, Any]:
        """POST order/id/ — часто требует авторизацию; session обязателен."""
        async with self._client() as client:
            sid = session or await self.fetch_session_id(client)
            r = await client.post(
                "/local/rest/front/order/id/",
                data={"session": sid, "id": str(order_id)},
            )
            r.raise_for_status()
            return _parse_json_safe(r.text)
