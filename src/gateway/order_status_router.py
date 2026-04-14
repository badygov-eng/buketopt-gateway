"""GET /api/v1/orders/{order_id} — прокси к Bitrix order/id/."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from gateway.bitrix_client import BitrixClient, BitrixRestError
from gateway.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["orders"])


def get_bitrix(settings: Settings = Depends(get_settings)) -> BitrixClient:
    return BitrixClient(settings)


@router.get(
    "/orders/{order_id}",
    summary="Карточка заказа (Bitrix order/id/)",
)
async def get_order(
    order_id: int,
    bitrix: BitrixClient = Depends(get_bitrix),
) -> dict[str, Any]:
    """Часто требует авторизацию в Bitrix; без токена может вернуть отказ."""
    try:
        return await bitrix.get_order_card(order_id)
    except BitrixRestError as e:
        logger.warning("order/id error: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
    except Exception as e:
        logger.exception("order/id unexpected")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
