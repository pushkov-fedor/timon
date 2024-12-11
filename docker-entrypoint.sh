#!/bin/bash
# ./docker-entrypoint.sh

export PYTHONPATH=$PYTHONPATH:/app

# Ждем, пока база данных станет доступна
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Применяем миграции
echo "Applying migrations..."
alembic upgrade head

# Запускаем приложение
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
