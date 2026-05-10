#!/bin/sh

echo "Waiting for database..."

sleep 3

echo "Running migrations..."
alembic upgrade head

echo "Starting FastAPI..."
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8000 --workers 4