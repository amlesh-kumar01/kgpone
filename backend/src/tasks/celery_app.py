from celery import Celery

# Instantiate the Celery app
celery_app = Celery("kgpone_worker")

# Load configuration from configuration module
celery_app.config_from_object("src.config.celery_config")

# Auto-discover tasks in the src.tasks module
celery_app.autodiscover_tasks(["src.tasks"])
