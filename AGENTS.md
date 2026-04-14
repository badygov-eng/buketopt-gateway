# AGENTS.md — buketopt-gateway

## Назначение

Шлюз принимает **JSON** от ботов / n8n / будущих маркетплейсов и оркеструет **HTTP-цепочку** к Битриксу без правок PHP на стороне сайта (вариант A).

## Правила

- **Секреты:** не в git; `GATEWAY_API_KEYS`, URL Битрикса — env или `~/.secrets/buketopt-gateway/`.
- **Таймауты:** все вызовы к Битриксу через `httpx` с `GATEWAY_BITRIX_HTTP_TIMEOUT_SEC`.
- **TLS:** на стенде часто `GATEWAY_BITRIX_VERIFY_TLS=false`.
- **Порты:** prod **8600** на `127.0.0.1` (за nginx/SSH при необходимости).
- **Деплой на прод-серверы:** только после явного «ДА, ДЕПЛОЙ» от владельца.
- **Язык:** комментарии и доки — русский.

## Код

- Пакет: `src/gateway/`.
- Точка входа ASGI: `gateway.app:app`.
- Клиент Битрикса: `bitrix_client.BitrixClient` (cookie jar на одну цепочку).

## Сценарии (согласовано с [rest-api-order.md в MCP](https://github.com/badygov-eng/MCP/blob/main/docs/buketopt-bitrix/rest-api-order.md))

- **Один клиент / одна сессия** на цепочку `session` → `basket/add` → **`order/checkout`** → **`order/create`**.
- **Самовывоз:** после `checkout` подставлять **`pickup_shop_val`** и **`time_range_value`** из ответа (активный слот).
- **Курьер:** валидный адрес и при необходимости **`address_data`** (DaData); опционально **`simple_order`** только осознанно (high-risk в Битриксе).
- **Оплата:** сопоставление **`payment_method_id`** с каталогом ПС; онлайн vs офлайн влияет на наличие **`payment_link`**, не на расчёт слотов (слоты от корзины + доставка + дата).
- Расширение JSON (**`payment_mode`**, явный вид заказа) — по желанию в шлюзе; в Битрикс уходит **`payment_method_id`** и поля формы.

## Тесты

```bash
pytest -q
```

E2E против стенда (сеть, реальные заказы): `GATEWAY_E2E=1 pytest -q tests/test_e2e_staging.py`.

## Если вариант A нестабилен

Запасной вариант B: один эндпоинт на Битриксе `local/rest/api/order/create/` — см. план проекта; этот репозиторий тогда переключается на один POST.
