#!/bin/bash
# ./scripts/run-tests.sh

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting test environment..."

# Запускаем тесты
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

# Сохраняем код возврата тестов
TEST_EXIT_CODE=$?

# Очищаем контейнеры и volumes
echo "🧹 Cleaning up test environment..."
docker compose -f docker-compose.test.yml down -v

# Выводим результат
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Tests passed successfully!${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
fi

# Возвращаем код возврата тестов
exit $TEST_EXIT_CODE 