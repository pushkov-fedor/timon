#!/bin/bash
# ./scripts/test.sh

# Запускаем тесты
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

# Сохраняем код возврата тестов
TEST_EXIT_CODE=$?

# Очищаем контейнеры и volumes
docker compose -f docker-compose.test.yml down -v

# Возвращаем код возврата тестов
exit $TEST_EXIT_CODE 