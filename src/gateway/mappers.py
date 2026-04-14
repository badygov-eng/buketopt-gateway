"""Маппинг OrderRequest → поля multipart для REST Битрикса."""

from __future__ import annotations

import json
from typing import Any

from gateway.config import Settings
from gateway.schemas import OrderRequest

# Допустимые значения `source` в Bitrix OrderFormData
_BITRIX_SOURCES = frozenset({"mobile", "site", "shop", "oneclick"})


def _bitrix_source(raw: str) -> str:
    if raw in _BITRIX_SOURCES:
        return raw
    return "site"


def order_request_to_form_fields(req: OrderRequest, settings: Settings) -> dict[str, Any]:
    """Плоский dict для `data=` в httpx (multipart form). Поле `session` добавляет BitrixClient."""
    payment_id = req.payment_method_id or settings.default_payment_method_id
    src = _bitrix_source(req.source)
    extra_comment = ""
    if req.source not in _BITRIX_SOURCES:
        extra_comment = f" [gateway_source:{req.source}]"

    fields: dict[str, Any] = {
        "allow_unauthorized": "1",
        "person_type": "natural",
        "user_name": req.customer_name,
        "user_phone": req.customer_phone,
        "user_email": req.customer_email or "",
        "recipient_name": req.recipient_name,
        "recipient_phone": req.recipient_phone,
        "delivery_type": req.delivery_type,
        "delivery_date": req.delivery_date,
        "time_range_value": req.time_range,
        "address_value": req.address,
        "flat": req.flat,
        "entrance": req.entrance,
        "payment_method_id": str(payment_id),
        "source": src,
        "user_comment": (req.comment + extra_comment).strip(),
    }

    if settings.use_simple_order:
        fields["simple_order"] = "1"

    if req.pickup_shop_val is not None:
        fields["pickup_shop_val"] = str(req.pickup_shop_val)

    # Минимальный address_data для курьера: на части стендов JSON-строка ломает PHP (implode);
    # для курьера без simple_order лучше передавать валидный DaData JSON с фронта.
    if req.delivery_type == "courier" and req.address.strip() and settings.use_simple_order:
        fields["address_data"] = json.dumps(
            {"value": req.address, "unrestricted_value": req.address},
            ensure_ascii=False,
        )
    return fields


def merge_bitrix_errors(payload: dict[str, Any]) -> list[str]:
    """Собрать человекочитаемые ошибки из тела ответа Bitrix."""
    out: list[str] = []
    if not payload.get("status", False):
        err = payload.get("error")
        if isinstance(err, dict):
            for k, v in err.items():
                out.append(f"{k}: {v}")
        elif isinstance(err, list):
            for x in err:
                if isinstance(x, dict):
                    out.append(str(x.get("message", x)))
                else:
                    out.append(str(x))
        elif err:
            out.append(str(err))
        data = payload.get("data")
        if isinstance(data, dict):
            fe = data.get("form_errors")
            if isinstance(fe, dict):
                for k, v in fe.items():
                    out.append(f"{k}: {v}")
            msg = data.get("message")
            if msg:
                out.append(str(msg))
    return out
