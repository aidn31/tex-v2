from fastapi import APIRouter, Depends, HTTPException

from services.clerk import get_current_user
from services.db import get_connection

router = APIRouter()


@router.get("")
async def list_notifications(user: dict = Depends(get_current_user)):
    """List notifications for the authenticated user, newest first.

    Returns all notifications (read and unread). Frontend can filter.
    Per CLAUDE.md: every query on a user-facing table includes WHERE user_id.
    """
    user_id = str(user["id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, report_id, type, message, read_at, created_at "
                "FROM notifications WHERE user_id = %s "
                "ORDER BY created_at DESC LIMIT 50",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": str(r[0]),
            "report_id": str(r[1]) if r[1] else None,
            "type": r[2],
            "message": r[3],
            "read_at": r[4].isoformat() if r[4] else None,
            "created_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a single notification as read."""
    user_id = str(user["id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE notifications SET read_at = now() "
                "WHERE id = %s AND user_id = %s AND read_at IS NULL",
                (notification_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """Mark all unread notifications as read for the authenticated user."""
    user_id = str(user["id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE notifications SET read_at = now() "
                "WHERE user_id = %s AND read_at IS NULL",
                (user_id,),
            )
        conn.commit()
    finally:
        conn.close()
    return {"status": "ok"}
