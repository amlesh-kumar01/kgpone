import os, sys
print('Starting Celery worker with auto-reload...')
sys.exit(os.system('uv run watchmedo auto-restart --directory=./src --pattern=*.py --recursive -- celery -A src.workers.app.celery_app worker --loglevel=info --pool=solo'))
