@echo off
title KgpOne Local Backend ^& Celery
echo ==============================================
echo  Starting KgpOne Backend ^& Celery (Local)
echo ==============================================
echo.

cd backend

echo [1/3] Applying Alembic Migrations...
call uv run alembic upgrade head

echo [2/3] Starting FastAPI Backend...
start "KgpOne API" cmd /k "uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting Celery Worker...
:: On Windows, Celery needs --pool=solo to work correctly
start "KgpOne Celery Worker" cmd /k "uv run celery -A src.workers.app.celery_app worker --loglevel=info --pool=solo"

echo.
echo All services have been started in separate windows!
echo Make sure your Redis URL in backend/.env points to your remote server.
cd ..
