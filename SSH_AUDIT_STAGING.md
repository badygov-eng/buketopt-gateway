# SSH-аудит стенда ai-test (85.239.60.199)

## База `db_buketai`

### Платёжные системы (ACTIVE=Y)

| ID | Название |
|----|----------|
| 15 | Сбербанк эквайринг (онлайн) |
| 1 | Наличные курьеру |
| … | см. полный список в отчёте агента |

По умолчанию в шлюзе: `GATEWAY_DEFAULT_PAYMENT_METHOD_ID=15`.

### Товары (примеры)

`product_id=296` — «Букет из 25 роз „Белый танец“» (подходит для E2E).

### askaron.settings

В `b_option` записей с `MODULE_ID=askaron.settings` не найдено; в коде используется `COption::GetOptionString("askaron.settings", ...)`.

### PHP `curl` на ai-test (исправлено 2026-04-14)

**Симптом:** `Call to undefined function curl_init()` при `order/create` (Loyalty и др.).

**Причина:** файл `/etc/php.d/20-curl.ini` был **пустым**; рабочее содержимое лежало в **`20-curl.ini.disabled`** (`extension=curl`). Пакет `php-common` уже содержит `curl.so`.

**Действие:** восстановлен `20-curl.ini` из `.disabled`, перезапущен **`httpd`**. Проверка CLI: `php -m` содержит `curl`.

**Смоук цепочки REST (сервер → `https://127.0.0.1`, Host `ai-test.buketopt.ru`, cookie-jar):** `session/get` → `basket/add` → `order/checkout` → `order/create` — успех, выданы `order_id` и `payment_link` (тестовый заказ на стенде).

> Боевой домен в ссылке оплаты может указывать на `buketopt.ru` — это настройки сайта в Битриксе, не параметр шлюза.
