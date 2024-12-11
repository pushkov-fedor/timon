#!/bin/bash
# ./scripts/run_tests.sh

# Ждем, пока база данных станет доступной
until nc -z $POSTGRES_HOST 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done
echo "PostgreSQL started"

# Применяем миграции
echo "Applying migrations..."
alembic upgrade head

# Запускаем тесты
pytest -v tests/
