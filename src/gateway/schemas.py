"""Pydantic-схемы API шлюза."""

from typing import Literal

from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    """Упрощённый JSON заказа (маппится в multipart Битрикса)."""

    product_id: int = Field(..., ge=1)
    quantity: int = Field(default=1, ge=1)
    customer_name: str = Field(..., min_length=1)
    customer_phone: str = Field(..., min_length=5)
    customer_email: str = ""
    recipient_name: str = Field(..., min_length=1)
    recipient_phone: str = Field(..., min_length=5)
    delivery_type: Literal["courier", "pickup"] = "courier"
    delivery_date: str = Field(..., description="DD.MM.YYYY")
    time_range: str = "default"
    address: str = ""
    flat: str = ""
    entrance: str = ""
    payment_method_id: int = Field(default=0, description="0 = взять из настроек шлюза")
    comment: str = ""
    source: str = "gateway"
    pickup_shop_val: int | None = Field(
        default=None,
        description="Код магазина (VALUE из pickup_shops_data) для delivery_type=pickup",
    )


class OrderResponse(BaseModel):
    """Ответ создания заказа."""

    order_id: int | None = None
    payment_link: str | None = None
    status: Literal["created", "error"] = "error"
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """/health."""

    status: str
    bitrix_reachable: bool
    bitrix_detail: str | None = None
