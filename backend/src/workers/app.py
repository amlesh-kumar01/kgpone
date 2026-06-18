from celery import Celery

# Instantiate the Celery app
celery_app = Celery("kgpone_worker")

# Load configuration from configuration module
celery_app.config_from_object("src.infrastructure.celery")

# Explicitly import the task modules so Celery can register them
celery_app.conf.imports = [
    "src.workers.tasks.ingestion_tasks",
    "src.workers.tasks.cleanup_tasks"
]
