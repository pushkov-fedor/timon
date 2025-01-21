# Timon API Documentation

## Overview

Timon API позволяет настраивать мониторинг Telegram-каналов и получать уведомления о новых постах через webhook.

## Основные концепции

1. **Channel (Канал)** - Telegram-канал, который мы мониторим. Один канал может иметь множество подписчиков.
2. **Subscription (Подписка)** - связь между каналом и callback URL, куда будут отправляться уведомления о новых постах.

## Endpoints

### Subscriptions

#### POST /subscriptions

Создает новую подписку на канал. Если канал еще не отслеживается, он будет добавлен автоматически.

**Request:**
```json
{
    "channel_url": "https://t.me/example_channel",
    "callback_url": "https://your-service.com/webhook"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "channel_id": 1,
    "callback_url": "https://your-service.com/webhook",
    "created_at": "2024-03-14T12:00:00Z",
    "is_active": true
}
```

**Errors:**
- 400 Bad Request - если подписка уже существует
- 500 Internal Server Error - если не удалось настроить мониторинг

#### DELETE /subscriptions/{subscription_id}

Деактивирует подписку. Если это была последняя активная подписка на канал, мониторинг канала будет остановлен.

**Response (204 No Content)**

**Errors:**
- 404 Not Found - если подписка не найдена

### Webhooks

#### POST /webhook/rss

Внутренний эндпоинт, который принимает данные от Huginn и рассылает их всем активным подписчикам канала.

**Webhook Payload (отправляется на callback_url):**
```json
{
    "title": "Заголовок поста",
    "link": "https://t.me/channel_name/123",
    "guid": "unique_post_id",
    "published_at": "2024-03-14T12:00:00Z",
    "text": "Текст поста без HTML",
    "links": [
        "https://example.com/link1",
        "https://example.com/link2"
    ],
    "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ],
    "videos": [
        "https://example.com/video1.mp4"
    ],
    "raw_content": "Исходный HTML контент"
}
```

## Примеры использования

### 1. Подписка на новый канал

```bash
curl -X POST http://api.timon.com/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "channel_url": "https://t.me/example_channel",
    "callback_url": "https://your-service.com/webhook"
  }'
```

### 2. Подписка второго сервиса на тот же канал

```bash
curl -X POST http://api.timon.com/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "channel_url": "https://t.me/example_channel",
    "callback_url": "https://another-service.com/webhook"
  }'
```

### 3. Отписка от канала

```bash
curl -X DELETE http://api.timon.com/subscriptions/1
```

## Жизненный цикл

1. Создание первой подписки на канал:
   - Создается запись канала в БД
   - Настраиваются Huginn агенты для мониторинга
   - Создается подписка

2. Создание дополнительных подписок:
   - Просто создается новая запись подписки
   - Существующие агенты продолжают работать

3. Удаление подписки:
   - Подписка деактивируется
   - Если это была последняя активная подписка:
     - Агенты Huginn удаляются
     - Канал помечается как не отслеживаемый

4. Получение нового поста:
   - Huginn отправляет пост в Timon
   - Timon находит все активные подписки канала
   - Пост отправляется на все callback URLs