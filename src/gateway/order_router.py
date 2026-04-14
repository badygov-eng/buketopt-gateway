"""POST /api/v1/orders."""

import logging

from fastapi import APIRouter, Depends

from gateway.bitrix_client import BitrixClient, BitrixRestError
from gateway.config import Settings, get_settings
from gateway.mappers import order_request_to_form_fields
from gateway.schemas import OrderRequest, OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["orders"])


def get_bitrix(settings: Settings = Depends(get_settings)) -> BitrixClient:
    return BitrixClient(settings)


@router.post(
    "/orders",
    response_model=OrderResponse,
    summary="Создать заказ (цепочка Bitrix REST)",
)
async def create_order(
    body: OrderRequest,
    settings: Settings = Depends(get_settings),
    bitrix: BitrixClient = Depends(get_bitrix),
) -> OrderResponse:
    """Маппинг JSON → multipart → session / basket / checkout / create."""
    form = order_request_to_form_fields(body, settings)
    try:
        return await bitrix.create_order_full_chain(body.product_id, body.quantity, form)
    except BitrixRestError as e:
        logger.warning("Bitrix chain error: %s", e)
        return OrderResponse(status="error", errors=[str(e)])
    except Exception as e:
        logger.exception("Unexpected error in create_order")
        return OrderResponse(status="error", errors=[str(e)])
