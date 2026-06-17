from celery import Celery

# Instantiate the Celery app
celery_app = Celery("kgpone_worker")

# Load configuration from configuration module
celery_app.config_from_object("src.infrastructure.celery")

# Auto-discover tasks in the src.workers.tasks module
celery_app.autodiscover_tasks(["src.workers.tasks"])
