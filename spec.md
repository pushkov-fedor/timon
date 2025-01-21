Ниже приведена окончательная спецификация проекта Timon и план разработки по спринтам, учитывая все предыдущие уточнения и новые требования о парсинге RSS-контента и отсутствии необходимости вручную создавать RSS ленту в RSSHub.

------------------------------------------

## Полная Спецификация

### 1. Введение

**Название проекта:** Timon

**Цель:**  
Создать сервис "Timon", который при получении ссылки на публичный Telegram-канал и `callback_url` от пользователя, настраивает мониторинг канала через RSSHub и Huginn. При появлении новых постов Timon будет автоматически пересылать данные о постах (включая разобранную структуру `description` с текстом, ссылками, изображениями) на указанный `callback_url`, не храня посты в своей БД.

### 2. Основная Логика

1. Пользователь через `POST /channels` отправляет `channel_url` и `callback_url`.
2. Timon извлекает `channel_username` из `channel_url` и сохраняет информацию о канале в БД.
3. Timon обращается к RSSHub по адресу `http://rsshub:1200/telegram/channel/<channel_username>?limit=100` для получения RSS ленты. Вручную ничего создавать в RSSHub не нужно — RSSHub автоматически генерирует ленту по запросу.
4. Timon через Huginn API (с использованием CSRF-токена) создаёт:
   - RSS Agent для мониторинга RSS-ленты канала
   - Post Agent для отправки данных в Timon
   - Связь между агентами
   Процесс создания включает:
   - Получение CSRF-токена с помощью GET запроса к странице агентов
   - Аутентификацию в Huginn
   - Создание агентов с использованием полученного токена
5. При появлении нового поста в канале Huginn вызывает `POST /webhook/rss` Timon, передавая данные поста (title, link, description, published, guid и т.д.).
6. Timon:
   - Из `link` извлекает `channel_username`.
   - Находит соответствующий канал в БД и его `callback_url`.
   - Разбирает `description` поста (HTML) с помощью HTML-парсера (BeautifulSoup или аналог) для извлечения:
     - Чистого текста поста.
     - Ссылок из `<a>`.
     - URL изображений из `<img>`.
     - Других необходимых данных (например, эмодзи, доп. контент).
   - После парсинга формирует структуру данных поста (title, link, guid, published_at, очищенный текст, массив ссылок, массив изображений).
   - Отправляет результат на `callback_url` пользователя (JSON).

7. Пользовательский сервис, получающий данные по `callback_url`, сохраняет и обрабатывает их по своему усмотрению.

### 3. Архитектура и Компоненты

- **Telegram-канал**: Источник информации.
- **RSSHub**: Автоматически генерирует RSS ленту канала по запросу (никакой ручной настройки).
- **Huginn**:  
  - RSS Agent читает RSS-ленту
  - Post Agent шлёт POST в Timon при новых постах
- **Timon (FastAPI)**:
  - `POST /channels`: Регистрация канала и `callback_url`
  - `POST /webhook/rss`: Приём новых постов от Huginn, парсинг `description`, пересылка на `callback_url`
- **PostgreSQL**:
  - Таблица `channels`: хранит `username`, `callback_url`, `huginn_rss_agent_id`, `huginn_post_agent_id`
  - Посты не хранятся.
- **Huginn API Интеграция**:
  - Аутентификация через `/users/sign_in`
  - Получение CSRF-токена из meta-тегов
  - Создание агентов через POST `/agents`
  - Управление агентами через соответствующие endpoints:
    - GET `/agents` для списка агентов
    - POST `/agents/{id}/handle_details_post` для ручных событий
    - POST `/agents/{id}/run` для запуска агента
    - DELETE `/agents/{id}` для удаления

### 4. Формат Данных

**POST /channels (request)**:
```json
{
  "channel_url": "https://t.me/s/example_channel",
  "callback_url": "https://user-service.com/my-webhook"
}
```

**POST /webhook/rss (request от Huginn к Timon)**:
```json
{
  "title": "New Post Title",
  "link": "https://t.me/example_channel/1234",
  "guid": "https://t.me/example_channel/1234",
  "description": "<p>Some HTML content with <a href='...'>links</a> and <img src='...'>images</img></p>",
  "published": "Wed, 11 Dec 2024 15:28:06 GMT"
}
```

**Timon → callback_url (POST)**:
```json
{
  "title": "New Post Title",
  "link": "https://t.me/example_channel/1234",
  "guid": "https://t.me/example_channel/1234",
  "published_at": "2024-12-11T15:28:06Z",
  "text": "Чистый текст поста без HTML",
  "links": ["http://...","http://..."],
  "images": ["http://...","http://..."]
  // Дополнительно можно расширять структуру по необходимости
}
```

**Huginn Agent Creation (Post)**:
```json
{
  "authenticity_token": "csrf_token",
  "agent": {
    "type": "Agents::PostAgent",
    "name": "Post - channel_username",
    "payload_mode": "merge",
    "options": {
      "post_url": "http://timon/webhook/rss",
      "expected_receive_period_in_days": "2",
      "content_type": "json",
      "method": "post",
      "payload": {
        "title": "{{title}}",
        "link": "{{url}}",
        "guid": "{{guid}}",
        "description": "{{description}}",
        "published": "{{published}}"
      }
    }
  },
  "commit": "Save"
}
```

### 5. Нефункциональные Требования

- Нет авторизации на данном этапе.
- Поддержка множества каналов, каждый с индивидуальными Huginn-агентами.
- Не хранить посты, только каналы и настройки агентов.
- Парсить `description` (HTML) для извлечения текстов, ссылок и изображений.
- RSSHub не требует ручного создания ленты, он генерирует её автоматически.

### 6. Тестирование

- Юнит-тесты: `/channels`, `/webhook/rss`, парсинг HTML.
- Интеграционные тесты: имитировать вызов Huginn → Timon, проверить отправку на `callback_url`.
- Проверить корректный парсинг `description`.

### 7. Развертывание

- `docker-compose` для Timon, PostgreSQL, RSSHub, Huginn.
- CI/CD через GitHub Actions.
- (Опционально) логирование ошибок, метрики.

------------------------------------------

## План Разработки по Спринтам

### Спринт 1: Базовая Инфраструктура и Добавление Каналов (Уже выполнен)

**Что было сделано:**
- Развёрнут PostgreSQL, RSSHub, Timon.
- Созданы миграции для `channels`.
- Реализован `POST /channels`: добавление канала в БД, извлечение `channel_username`, возврат `id` и `message`.

**Результат Спринта 1:**
- Каналы можно добавлять через API.
- RSSHub доступен.
- Инфраструктура готова.

### Спринт 2: Динамическая Интеграция с Huginn

**Цели:**
- При добавлении канала автоматически создавать RSS и Post агентов в Huginn через его API
- Связывать RSS Agent с Post Agent

**Задачи:**
1. Реализовать класс HuginnClient для работы с API:
   - Аутентификация
   - Управление CSRF-токенами
   - Методы для создания/удаления агентов
2. После `POST /channels`:
   - Получить CSRF-токен
   - Создать RSS Agent с правильными параметрами
   - Создать Post Agent с настроенным URL и форматированием payload
   - Связать агентов
3. Сохранить ID созданных агентов в БД
4. Добавить обработку ошибок при работе с Huginn API
5. Реализовать cleanup при удалении канала

**Результат Спринта 2:**
- При добавлении нового канала Timon автоматически настраивает Huginn для мониторинга канала.

### Спринт 3: Обработка Новых Постов и Парсинг HTML

**Цели:**
- Реализовать `POST /webhook/rss`: получать новые посты от Huginn, парсить `description`.
- Извлекать из `description` текст, ссылки, изображения.
- Отправлять результат на `callback_url`.

**Задачи:**
1. Реализовать `POST /webhook/rss`:
   - Получать `title`, `link`, `guid`, `description`, `published`.
   - По `link` извлечь `channel_username`.
   - Найти `callback_url` по `channel_username` в БД.
2. Парсинг `description`:
   - Использовать HTML-парсер (BeautifulSoup).
   - Извлечь чистый текст, ссылки (`<a>`), изображения (`<img>`).
3. Сформировать структуру поста и сделать POST на `callback_url` со всеми извлечёнными данными.
4. Тестирование корректного парсинга и пересылки данных.

**Результат Спринта 3:**
- Новые посты автоматически пересылаются на вебхук пользователя с уже разобранным содержимым.

### Спринт 4: Поддержка Множественных Подписок

**Цели:**
- Обеспечить возможность подписки нескольких пользователей на один канал
- Реорганизовать структуру БД для корректной работы с подписками
- Оптимизировать работу с Huginn агентами

**Изменения в структуре БД:**

1. Таблица `channels`:
```sql
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_monitored BOOLEAN DEFAULT TRUE,
    huginn_rss_agent_id INTEGER,
    huginn_post_agent_id INTEGER  -- один Post Agent на канал
);
```

2. Новая таблица `subscriptions`:
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id),
    callback_url VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(channel_id, callback_url)
);
```

**Флоу работы:**
1. При создании первой подписки на канал:
   ```
   1. Создаём канал
   2. Создаём RSS Agent
   3. Создаём один Post Agent
   4. Связываем RSS Agent -> Post Agent -> наш webhook
   5. Создаём запись в subscriptions
   ```

2. При создании последующих подписок:
   ```
   1. Находим существующий канал
   2. Создаём только запись в subscriptions
   ```

3. При получении webhook от Post Agent:
   ```
   1. Определяем канал из данных поста
   2. Находим все активные подписки канала
   3. Отправляем данные на все callback_url
   ```

4. При отписке:
   ```
   1. Деактивируем подписку
   2. Если нет активных подписок:
      - Удаляем RSS Agent и Post Agent
      - Канал удаляем
   ```

**Преимущества:**
1. Оптимальное использование Huginn агентов (один RSS + один Post на канал)
2. Правильная структура БД с отдельной таблицей подписок
3. Простое масштабирование
4. Чёткое разделение данных каналов и подписок

------------------------------------------

## Итог

После выполненного Спринта 1, во втором спринте добавляем динамическую интеграцию с Huginn.  
В третьем спринте реализуем приём новых постов, парсинг HTML и пересылку результатов на `callback_url`.

Таким образом, Timon становится сервисом, который по запросу настроит слежение за Telegram-каналом и будет автоматически пересылать новые посты (в разобранном виде) на указанный пользователем вебхук.