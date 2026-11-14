# receipt-bot

Сервис выдаёт чек об оплате по **реальному платежу**: платёжный провайдер присылает вебхук,
сервис сохраняет платёж, бот отправляет пользователю ссылку на страницу чека.
QR на чеке ведёт на страницу проверки, которая подтверждает, что платёж есть в вашей базе.
Создать чек вручную (через бота или иначе) нельзя.

## Структура

```
app/
  main.py          фабрика приложения: FastAPI + запуск бота в одном процессе
  config.py        настройки из переменных окружения
  db.py            SQLite (aiosqlite): платежи
  security.py      HMAC-подписи вебхука и ссылок
  links.py         сборка подписанных ссылок на чек и проверку
  formatting.py    суммы и даты
  bot/             aiogram: /start, /receipts, клавиатуры
  web/             роуты (вебхук, чек, проверка), шаблоны, стили
tests/             pytest
scripts/           send_test_webhook.py для локальной проверки
```

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # заполнить значения
uvicorn app.main:create_app --factory --port 8000
```

Или через Docker: `docker compose up -d --build`.

Telegram принимает кнопки со ссылками только на публичный HTTPS. Для локальной отладки
откройте туннель (ngrok, Cloudflare Tunnel) и поставьте его адрес в `BASE_URL`.

## Проверка вручную

1. Напишите боту `/start`, чтобы Telegram разрешил ему писать вам.
2. Узнайте свой id (например, через @userinfobot).
3. `python scripts/send_test_webhook.py <ваш_id> 5300`
4. В чате придёт кнопка «Открыть чек».

## Вебхук

`POST /webhook/payment`, заголовок `X-Signature` = HMAC-SHA256 от тела запроса ключом `WEBHOOK_SECRET`.

```json
{"payment_id": "pay_0001", "tg_user_id": 123456789, "amount_kop": 5300,
 "description": "Оплата услуги", "paid_at": 1763150000}
```

`paid_at` необязателен (unix time). Повторный вебхук с тем же `payment_id` не создаёт дубль
и не шлёт второе уведомление.

Реальные провайдеры (ЮKassa, CloudPayments и др.) используют свой формат тела и подписи.
Подстройте `PaymentEvent` и проверку в `app/web/routes.py` под их документацию,
а `tg_user_id` передавайте в метаданных платежа при его создании.

## Ссылки и безопасность

- `/r/{id}?sig=...` и `/verify/{id}?sig=...` подписаны `LINK_SECRET`; подпись для чека не подходит для проверки.
- Без валидной подписи по `payment_id` ничего не угадать.
- Секреты вебхука и ссылок разные, храните их только в `.env`.

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```
