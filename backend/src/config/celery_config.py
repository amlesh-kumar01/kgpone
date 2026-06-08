import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Serialization settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Task result expiration (e.g. 1 hour)
result_expires = 3600

# Worker tuning settings
worker_prefetch_multiplier = 1
task_track_started = True
task_send_sent_event = True
