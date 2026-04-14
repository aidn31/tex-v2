import logging
import os

from celery import Celery
from celery.signals import worker_ready
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
    broker_transport_options={
        "visibility_timeout": 10800,  # 3 hours — large films in Docker can take 2+ hrs
    },
)

celery_app.conf.task_queues = (
    Queue("film_processing"),
    Queue("report_generation"),
    Queue("section_generation"),
    Queue("notifications"),
)
celery_app.conf.task_default_queue = "notifications"

log = logging.getLogger(__name__)


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Run startup recovery on every worker boot.

    Safe during rolling deploys — task idempotency (check status before acting)
    means a re-enqueued task that is actually still running exits immediately.
    """
    recover_stuck_jobs()


def recover_stuck_jobs():
    """Find jobs stuck in 'processing' beyond 2x their hard timeout and re-enqueue.

    Thresholds per AGENTS.md:
      films:   2 hours  (2x the 60-min film_processing hard limit)
      reports: 1 hour   (2x the 30-min report_generation hard limit)
    """
    # Late imports to avoid circular dependency — celery_app is imported by task files.
    from services.db import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Stuck films
            cur.execute(
                "SELECT id FROM films "
                "WHERE status = 'processing' "
                "AND updated_at < now() - interval '2 hours' "
                "AND deleted_at IS NULL"
            )
            stuck_films = cur.fetchall()

            # Stuck reports
            cur.execute(
                "SELECT id FROM reports "
                "WHERE status = 'processing' "
                "AND updated_at < now() - interval '1 hour' "
                "AND deleted_at IS NULL"
            )
            stuck_reports = cur.fetchall()
    finally:
        conn.close()

    # Re-enqueue stuck films.
    if stuck_films:
        from tasks.film_processing import process_film
        for (film_id,) in stuck_films:
            process_film.delay(str(film_id))
            log.info("Startup recovery: re-enqueued stuck film %s", film_id)

    # Re-enqueue stuck reports.
    if stuck_reports:
        from tasks.report_generation import generate_report
        for (report_id,) in stuck_reports:
            generate_report.delay(str(report_id))
            log.info("Startup recovery: re-enqueued stuck report %s", report_id)

    total = len(stuck_films) + len(stuck_reports)
    if total:
        log.info("Startup recovery complete: %d films, %d reports re-enqueued",
                 len(stuck_films), len(stuck_reports))
    else:
        log.info("Startup recovery: no stuck jobs found")
