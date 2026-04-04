import os

from celery import Celery
from kombu import Queue

celery_app = Celery(
    "tex",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "tasks.film_processing",
        "tasks.report_generation",
        "tasks.section_generation",
        "tasks.notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_queues = (
    Queue("film_processing"),
    Queue("report_generation"),
    Queue("section_generation"),
    Queue("notifications"),
)
celery_app.conf.task_default_queue = "notifications"
