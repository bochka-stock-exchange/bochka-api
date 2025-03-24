#!/bin/sh
echo "Waiting for database migrations to apply..."

until uv run alembic upgrade head; do
  echo "Waiting for migrations to apply..."
  sleep 2
done

echo "Migrations applied. Running tests..."

exec uv run pytest -v --durations=0 --cov --cov-report=xml "$@"
