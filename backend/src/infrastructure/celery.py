from src.config.settings import Settings

broker_url = Settings.CELERY_BROKER_URL
result_backend = Settings.CELERY_RESULT_BACKEND

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
