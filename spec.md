Ниже приведена откорректированная спецификация и план разработки по спринтам с учётом новых вводных:  
- Проект называется **Timon**  
- Используем **FastAPI** в качестве веб-фреймворка.

------------------------------------------

## Полная Спецификация

### 1. Введение

**Название проекта:** Timon

**Цель:** Создать автономный сервис "Timon", который принимает ссылку на публичный Telegram-канал, настраивает слежение за его постами через RSSHub и Huginn, сохраняет все новые посты в базу данных и предоставляет REST API для их получения в удобном формате.

**Основная логика:**  
- Пользователь отправляет Timon ссылку на Telegram-канал.  
- Timon извлекает имя канала (`channel_username`) и сохраняет данные о канале в БД.  
- RSSHub генерирует RSS-ленту по каналу.  
- Huginn мониторит RSS-ленту. При появлении новых постов Huginn шлёт вебхук в Timon.  
- Timon принимает вебхук, извлекает данные о посте, сохраняет их в БД.  
- Пользователь может получить посты канала через API Timon.

### 2. Архитектура и Компоненты

1. **Telegram-канал:** Источник данных (публичный канал).

2. **RSSHub (Open Source):**  
   Превращает публичный Telegram-канал в RSS-ленту.  
   Пример маршрута: `http://<rsshub_host>/telegram/channel/<channel_username>?limit=100`

3. **Huginn (Open Source):**  
   Инструмент автоматизации.  
   - RSS Agent отслеживает RSS-ленту канала.  
   - Webhook Agent отправляет POST запросы в Timon при появлении новых постов.

4. **Timon (Back-end сервис, FastAPI):**  
   - Написан на Python, используя FastAPI.  
   - Основные эндпоинты:  
     - `POST /channels` – добавление канала  
     - `POST /webhook/rss` – приём данных о новых постах от Huginn  
     - `GET /api/posts` – получение постов канала

   Функционал Timon:
   - При добавлении канала – сохранение информации о канале в БД.  
   - При получении вебхука от Huginn – сохранение поста в БД (если нет дубликата).

5. **База Данных (PostgreSQL):**  
   Таблицы:
   ```sql
   CREATE TABLE channels (
     id SERIAL PRIMARY KEY,
     username TEXT UNIQUE NOT NULL,
     created_at TIMESTAMP DEFAULT NOW(),
     is_monitored BOOLEAN DEFAULT TRUE
   );

   CREATE TABLE posts (
     id SERIAL PRIMARY KEY,
     channel_id INTEGER REFERENCES channels(id),
     title TEXT,
     link TEXT,
     published_at TIMESTAMP,
     content TEXT,
     guid TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     UNIQUE(channel_id, guid)
   );
   ```

### 3. Формат Данных

**POST /channels (request):**  
```json
{
  "channel_url": "https://t.me/s/example_channel"
}
```

**POST /webhook/rss (request):**  
Пример данных от Huginn:  
```json
{
  "title": "New Post Title",
  "link": "https://t.me/example_channel/1234",
  "guid": "https://t.me/example_channel/1234",
  "description": "<p>Some HTML content</p>",
  "published": "Wed, 11 Dec 2024 15:28:06 GMT"
}
```

**GET /api/posts (response):**  
```json
[
  {
    "title": "New Post Title",
    "link": "https://t.me/example_channel/1234",
    "published_at": "2024-12-11T15:28:06Z",
    "content": "<p>Some HTML content</p>"
  }
]
```

Параметры для `/api/posts`:  
`channel` (строка), `limit` (число).

Пример запроса:  
`GET /api/posts?channel=example_channel&limit=50`

### 4. Логика Обработки

1. Пользователь вызывает `POST /channels` с URL канала.  
   - Timon извлекает `channel_username` из URL, сохраняет канал в БД.

2. RSSHub:  
   - По адресу `http://rsshub:1200/telegram/channel/<channel_username>?limit=100` доступна RSS-лента.

3. Huginn:  
   - Настраивается RSS Agent на ленту из RSSHub.  
   - Настраивается Webhook Agent, который при новых постах посылает POST на `POST /webhook/rss` Timon.

4. Timon при получении вебхука:  
   - По `link` извлекает `channel_username`.  
   - Находит `channel_id` в БД.  
   - Проверяет, есть ли пост с таким `guid`. Если нет – сохраняет новый пост.

5. Пользователь через `GET /api/posts` получает список постов.

### 5. Нефункциональные Требования

- Открытый стек: FastAPI, PostgreSQL, RSSHub, Huginn (все open-source).  
- Масштабируемость: при необходимости можно добавить кэширование.  
- Быстрая реализация MVP с возможностью дальнейшего расширения.  
- FastAPI даёт автоматическую документацию по OpenAPI, удобную типизацию и валидацию данных.

### 6. Тестирование

- Юнит-тесты для эндпоинтов `/channels`, `/webhook/rss`.
- Интеграционные тесты: проверить цепочку RSSHub → Huginn → Timon.
- Проверка возвращаемых данных `/api/posts`.

### 7. Развертывание

- Используем `docker-compose` для Timon, PostgreSQL, RSSHub, Huginn.
- CI/CD через GitHub Actions для автоматического деплоя.
- Возможна интеграция с Sentry для логирования ошибок и Prometheus+Grafana для метрик.

------------------------------------------

## План Разработки по Спринтам

### Спринт 1: Базовая Инфраструктура и Добавление Каналов

**Цели:**
- Развернуть PostgreSQL и RSSHub.
- Настроить структуру базы (миграции).
- Реализовать `POST /channels` в Timon на FastAPI.

**Задачи:**
1. Создать `docker-compose.yml` для PostgreSQL, Timon (FastAPI) и RSSHub.
2. Написать миграции для `channels` и `posts`.
3. Реализовать эндпоинт `/channels`:
   - Принимать `channel_url`.
   - Извлекать `channel_username`.
   - Сохранять запись в `channels`.
   - Возвращать JSON с `id` и `message`.

**Результат Спринта 1:**
- Каналы можно добавлять через API.
- RSSHub доступен.
- Инфраструктура (DB, App, RSSHub) готова.

### Спринт 2: Интеграция с Huginn и Вебхук

**Цели:**
- Развернуть Huginn.
- Настроить RSS Agent и Webhook Agent.
- Реализовать `POST /webhook/rss` для приёма новых постов.

**Задачи:**
1. Добавить Huginn в `docker-compose`.
2. В интерфейсе Huginn:
   - Создать RSS Agent на URL RSSHub.
   - Создать Webhook Agent, указывающий `/webhook/rss`.
   - Связать их.
3. Реализовать в Timon `/webhook/rss`:
   - Принимать `title`, `link`, `guid`, `description`, `published`.
   - Из `link` извлечь `channel_username`.
   - Найти `channel_id`.
   - Проверить дубликат по `(channel_id, guid)`.
   - Сохранить новый пост, если он уникален.

**Результат Спринта 2:**
- Автоматическая запись новых постов из каналов в БД.

### Спринт 3: API для Получения Постов

**Цели:**
- Предоставить `GET /api/posts` для получения постов канала.

**Задачи:**
1. Реализовать `GET /api/posts?channel=example_channel&limit=50`:
   - По `channel` найти `channel_id`.
   - Выбрать последние `limit` постов, отсортировать по `published_at` DESC.
   - Вернуть JSON массив с нужными полями.
2. Добавить простые тесты на `/api/posts`.

**Результат Спринта 3:**
- Пользователь может получать список постов через API Timon.

### Спринт 4: Опциональные Улучшения

**Цели:**
- Улучшить функционал, масштабируемость, удобство.

**Задачи (опционально):**
1. Добавить фильтрацию по дате: `GET /api/posts?channel=...&after=...`.
2. Внедрить аутентификацию к эндпоинтам (Bearer токен).
3. Парсить HTML в `description` для получения чистого текста.
4. Автоматизировать настройку Huginn Agents через его API при добавлении канала.

**Результат Спринта 4:**
- Расширенные возможности и улучшенный опыт для пользователей.

------------------------------------------

## Итог

После выполнения первых трёх спринтов сервис Timon будет готов к использованию:  
- Можно добавлять каналы (`/channels`).  
- Новые посты будут автоматически появляться в БД через RSSHub и Huginn (`/webhook/rss`).  
- Можно получить посты канала через `/api/posts`.

Спринт 4 предоставит улучшения и новые возможности по мере необходимости.