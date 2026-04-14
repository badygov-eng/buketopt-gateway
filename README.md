# buketopt-gateway

Сервис-шлюз **FastAPI** для создания заказов на сайте **1С-Битрикс** через существующий REST `/local/rest/front/` (вариант A: цепочка `session/get` → `basket/add` → `order/checkout` → `order/create`).

Отдельный репозиторий; исходный импорт из монорепо **[badygov-eng/MCP](https://github.com/badygov-eng/MCP)** (каталог `buketopt-gateway/`). Документация по Битриксу по-прежнему в MCP, см. ссылки ниже.

## Быстрый старт (локально)

```bash
cd buketopt-gateway
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export GATEWAY_API_KEYS=dev-key
export GATEWAY_BITRIX_BASE_URL=https://ai-test.buketopt.ru
export GATEWAY_BITRIX_VERIFY_TLS=false
uvicorn gateway.app:app --reload --app-dir src --port 8600
```

- Документация API: http://127.0.0.1:8600/docs
- Health: http://127.0.0.1:8600/health

## Секреты

Канонично: `~/.secrets/buketopt-gateway/` (env-файл без коммита). Переменные см. `.env.example`.

## Docker

```bash
docker compose up --build
```

По умолчанию в `docker-compose.yml` проброшен `127.0.0.1:8600:8600`.

## API

- `POST /api/v1/orders` — тело JSON (`OrderRequest`), заголовок `X-Api-Key`.
- `GET /api/v1/orders/{order_id}` — прокси к Bitrix `order/id/` (часто нужна авторизация на стороне Битрикса).
- `GET /health` — доступность Bitrix (`session/get`).

## Аудит стенда

Сводка SSH-аудита **ai-test** (платёжные системы, примеры `product_id`): файл **`SSH_AUDIT_STAGING.md`** в корне репозитория (если файл не в git — см. историю / создайте из README).

## Деплой

Только после явного согласования (**«ДА, ДЕПЛОЙ»**). Скрипт `scripts/deploy-prod.sh` — шаблон под **main-server YC**, порт **8600** (loopback).

## Сценарии заказа (контракт Битрикса)

- **Доставка:** `delivery_type=courier` \| **Самовывоз:** `pickup` + `pickup_shop_val` из ответа `order/checkout`.
- **Интервалы:** брать **`time_range_value`** из активных **`time_ranges`** после `order/checkout`, не полагаться на `default` без проверки.
- **Оплата:** задаётся **`payment_method_id`**; онлайн — часто есть **`payment_link`** в ответе `order/create`; офлайн/счёт/маркетплейс — ссылки может не быть, оплата вне этого запроса.

Подробно: [rest-api-order.md в MCP](https://github.com/badygov-eng/MCP/blob/main/docs/buketopt-bitrix/rest-api-order.md) (§4.6–4.7, §6).

## Связанные документы (монорепо MCP)

- [rest-api-order.md](https://github.com/badygov-eng/MCP/blob/main/docs/buketopt-bitrix/rest-api-order.md) — контракт REST, сценарии и оплата.
- [openapi-rest-front-orders.yaml](https://github.com/badygov-eng/MCP/blob/main/docs/buketopt-bitrix/openapi-rest-front-orders.yaml) — черновик OpenAPI.
- [snippets/catalog-api-create/](https://github.com/badygov-eng/MCP/tree/main/docs/buketopt-bitrix/snippets/catalog-api-create) — PHP `/local/rest/api/catalog/create/` (контракт с картинкой base64 на ai-test).
