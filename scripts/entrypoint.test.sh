#!/bin/bash
# ./scripts/entrypoint.test.sh

# Ждем, пока база данных станет доступной
until nc -z $POSTGRES_HOST 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done
echo "PostgreSQL started"

# Применяем миграции
echo "Applying migrations..."
alembic upgrade head

# Запускаем тесты с покрытием
pytest -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:coverage_report \
    tests/
