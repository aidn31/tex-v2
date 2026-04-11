import logging

from tasks.celery_app import celery_app
from services.db import get_connection

log = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.notifications.notify_coach",
    queue="notifications",
    max_retries=3,
    default_retry_delay=5,
    soft_time_limit=25,
    time_limit=30,
    acks_late=True,
)
def notify_coach(self, report_id: str = None, film_id: str = None,
                 notification_type: str = "report_complete"):
    """Write a notification row for a coach. Phase 2 stub — full implementation in Phase 3."""
    NOTIFICATION_MESSAGES = {
        "report_complete": "Your scouting report is ready. Download it now.",
        "report_partial": "Your report is ready with some sections incomplete.",
        "report_failed_credit_applied": (
            "Your report could not be completed. "
            "A free report credit has been added to your account."
        ),
        "film_error": "Your film could not be processed. Please re-upload or contact support.",
    }

    message = NOTIFICATION_MESSAGES.get(notification_type, "You have a new notification.")

    # Determine user_id from film or report
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            user_id = None
            if film_id:
                cur.execute("SELECT user_id, error_message FROM films WHERE id = %s", (film_id,))
                row = cur.fetchone()
                if row:
                    user_id = row[0]
                    if notification_type == "film_error" and row[1]:
                        message = f"Your film could not be processed: {row[1]}. Please re-upload or contact support."
            elif report_id:
                cur.execute("SELECT user_id FROM reports WHERE id = %s", (report_id,))
                row = cur.fetchone()
                if row:
                    user_id = row[0]

            if not user_id:
                log.warning("notify_coach: could not determine user_id for film_id=%s report_id=%s", film_id, report_id)
                return

            cur.execute(
                "INSERT INTO notifications (user_id, report_id, type, message) "
                "VALUES (%s, %s, %s, %s)",
                (str(user_id), report_id, notification_type, message),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise self.retry(exc=exc)
    finally:
        conn.close()
