"""FastAPI-приложение."""

import logging

from fastapi import Depends, FastAPI

from gateway import __version__
from gateway.auth import ApiKeyMiddleware
from gateway.bitrix_client import BitrixClient
from gateway.config import Settings, get_settings
from gateway.order_router import router as order_router
from gateway.order_status_router import router as order_status_router
from gateway.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="buketopt-gateway",
    version=__version__,
    description="Шлюз заказов → REST Битрикса `/local/rest/front/`",
)

app.add_middleware(ApiKeyMiddleware)
app.include_router(order_router)
app.include_router(order_status_router)


@app.get("/health", response_model=HealthResponse, tags=["service"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Проверка процесса и доступности Bitrix (session/get)."""
    client = BitrixClient(settings)
    ok, detail = await client.ping()
    return HealthResponse(
        status="ok" if ok else "degraded",
        bitrix_reachable=ok,
        bitrix_detail=detail,
    )
