# Webhook «новая заявка»

Сайт отправляет HTTP-уведомление о каждой новой заявке на адреса, настроенные в панели управления («Webhook: приёмники») или в переменной `WEBHOOK_URL`. Подключение конкретной CRM/1С в объём не входит (ТЗ 5.2): это документированный формат, который принимающая сторона реализует самостоятельно.

## Запрос

- Метод `POST`, `Content-Type: application/json; charset=utf-8`, тело — JSON в UTF-8.
- Заголовки:

| Заголовок | Значение |
|---|---|
| `X-Dortech-Event` | `inquiry.created` |
| `X-Dortech-Delivery` | UUID доставки; при повторах не меняется (ключ идемпотентности) |
| `X-Dortech-Timestamp` | Unix-время отправки, секунды |
| `X-Dortech-Signature` | `sha256=<hex HMAC-SHA256(secret, timestamp + "." + body)>` |
| `User-Agent` | `Dortech-Webhook/1.0` |

- Таймаут 10 с. Успех — любой ответ 2xx. При ошибке или недоступности повторы через 1 мин, 5 мин, 30 мин, 2 ч, 12 ч, 24 ч; затем доставка помечается как «ошибка», администратор может переотправить её из панели.

## Тело

```json
{
  "id": "4d2f0a7e-…",
  "event": "inquiry.created",
  "created_at": "2026-11-05T09:12:33+00:00",
  "data": {
    "public_id": "d4460acb-…",
    "number": "DT-000123",
    "status": "new",
    "status_label": "Новая",
    "source": "web",
    "created_at": "2026-11-05T09:12:33+00:00",
    "organization": {"id": 12, "name": "ООО «Пример»"},
    "company_name": "ООО «Пример»",
    "contact": {"name": "Иванов Иван", "phone": "+7 900 000-00-00", "email": "ivanov@example.com"},
    "period": {"from": "2026-11-10", "to": "2026-11-14"},
    "work_place": "г. Самара, ул. Примерная, 1",
    "comment": "Нужен машинист",
    "items": [
      {"equipment_id": 7, "name": "Экскаватор Komatsu PC200", "model": "PC200", "quantity": 1, "units": 5, "unit": "shift",
       "unit_price": "12000.00", "line_total": "60000", "needs_quote": false}
    ],
    "extra_services": [{"id": 1, "name": "Доставка техники на объект", "price": "15000.00"}],
    "estimate": {"total": "75000", "currency": "RUB", "is_partial": false, "vat_label": "без НДС"},
    "links": {"manager_url": "https://site/manager/inquiries/d4460acb-…"}
  }
}
```

`source`: `web` — публичная форма, `account` — из кабинета, `repeat` — повтор заявки. `unit`: `shift` (смена) или `day` (сутки). Суммы — строки с десятичной точкой; `needs_quote: true` — позиция без цены (по запросу), тогда `estimate.is_partial = true`.

## Проверка подписи (Python)

```python
import hashlib, hmac, time

def verify(secret: str, headers: dict, body: bytes, max_age: int = 300) -> bool:
    ts = headers.get("X-Dortech-Timestamp", "")
    if not ts.isdigit() or abs(time.time() - int(ts)) > max_age:
        return False
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(headers.get("X-Dortech-Signature", ""), f"sha256={mac}")
```

Рекомендации приёмнику: отвечать 2xx сразу и обрабатывать асинхронно; хранить `X-Dortech-Delivery`, чтобы игнорировать повторы; отклонять запросы старше 5 минут.

## Проверка при приёмке

На тестовой среде включён встроенный приёмник `POST /api/v1/webhook-sink` (`WEBHOOK_SINK_ENABLED=1`), который проверяет подпись и показывает принятые доставки в панели («Webhook: тестовый приёмник»). Для проверки достаточно указать его адрес в «Webhook: приёмники» с тем же секретом, что в `WEBHOOK_SECRET`.
