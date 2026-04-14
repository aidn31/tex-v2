import os
import logging

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    ReportCreate,
    ReportCreateResponse,
    ReportDetailResponse,
    ReportResponse,
    SectionStatus,
)
from services.clerk import get_current_user
from services.db import get_connection
from services.payment_gate import (
    CREDIT,
    FREE,
    STRIPE_REQUIRED,
    check_payment_gate,
    consume_entitlement,
)
from services.prompts import load_prompt
from services.r2 import generate_presigned_read_url

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_prompt_version() -> str:
    """Read the current prompt version from disk. All 6 prompts share a version."""
    _, version = load_prompt("offensive_sets")
    return version


@router.post("", response_model=ReportCreateResponse, status_code=201)
async def create_report(
    body: ReportCreate, user: dict = Depends(get_current_user)
):
    """Create a scouting report for the given team and films.

    Checks the payment gate:
      - free (first report): creates report, enqueues generation
      - credit: consumes a credit, creates report, enqueues generation
      - stripe_required: returns payment_required=True so frontend
        redirects the coach to Stripe checkout

    Per CLAUDE.md PAYMENT RULES: payment gate fires before report
    generation starts, not after.
    """
    user_id = str(user["id"])

    if not body.film_ids:
        raise HTTPException(status_code=400, detail="At least one film_id is required")

    # Validate team belongs to user.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM teams "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (body.team_id, user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Team not found")
    finally:
        conn.close()

    # Validate all films belong to user and team, and are processed.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status FROM films "
                "WHERE id = ANY(%s::uuid[]) AND team_id = %s "
                "AND user_id = %s AND deleted_at IS NULL",
                (body.film_ids, body.team_id, user_id),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    found_ids = {str(r[0]) for r in rows}
    if found_ids != set(body.film_ids):
        raise HTTPException(status_code=404, detail="One or more films not found")

    not_processed = [str(r[0]) for r in rows if r[1] != "processed"]
    if not_processed:
        raise HTTPException(
            status_code=400,
            detail="Films must be fully processed before generating a report",
        )

    # Check payment gate.
    path = check_payment_gate(user_id)
    if path == STRIPE_REQUIRED:
        return ReportCreateResponse(payment_required=True)

    # Free or credit path — create report in a single transaction.
    prompt_version = _get_prompt_version()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Insert report row.
            cur.execute(
                "INSERT INTO reports (user_id, team_id, prompt_version, status) "
                "VALUES (%s, %s, %s, 'pending') RETURNING id",
                (user_id, body.team_id, prompt_version),
            )
            report_id = str(cur.fetchone()[0])

            # 2. Insert report_films join rows.
            for film_id in body.film_ids:
                cur.execute(
                    "INSERT INTO report_films (report_id, film_id) VALUES (%s, %s)",
                    (report_id, film_id),
                )

            # 3. Consume entitlement (increment reports_used, decrement credit if needed).
            consume_entitlement(cur, user_id, path)

        conn.commit()
    except ValueError as exc:
        # consume_entitlement raises ValueError on race (credits exhausted).
        conn.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    finally:
        conn.close()

    # Enqueue after commit — worker must see the reports row.
    from tasks.report_generation import generate_report
    generate_report.delay(report_id)

    logger.info(
        "Report created via %s path",
        path,
        extra={"report_id": report_id, "user_id": user_id, "path": path},
    )

    return ReportCreateResponse(report_id=report_id, payment_required=False)


REPORT_COLUMNS = (
    "id, team_id, status, title, prompt_version, error_message, "
    "generation_time_seconds, completed_at, created_at, updated_at"
)


def _row_to_response(row) -> ReportResponse:
    return ReportResponse(
        id=str(row[0]),
        team_id=str(row[1]),
        status=row[2],
        title=row[3],
        prompt_version=row[4],
        error_message=row[5],
        generation_time_seconds=row[6],
        completed_at=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(user: dict = Depends(get_current_user)):
    """List all reports for the authenticated user, newest first."""
    user_id = str(user["id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {REPORT_COLUMNS} FROM reports "
                "WHERE user_id = %s AND deleted_at IS NULL "
                "ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [_row_to_response(r) for r in rows]


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Get a single report with section progress and presigned PDF URL.

    Per CLAUDE.md: every query on a user-facing table includes WHERE user_id.
    """
    user_id = str(user["id"])

    # Fetch report.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {REPORT_COLUMNS}, pdf_r2_key FROM reports "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (report_id, user_id),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    report = _row_to_response(row)
    pdf_r2_key = row[10]

    # Fetch section statuses.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT section_type, status, model_used, generation_time_seconds "
                "FROM report_sections WHERE report_id = %s "
                "ORDER BY created_at",
                (report_id,),
            )
            section_rows = cur.fetchall()
    finally:
        conn.close()

    sections = [
        SectionStatus(
            section_type=r[0],
            status=r[1],
            model_used=r[2],
            generation_time_seconds=r[3],
        )
        for r in section_rows
    ]

    # Generate presigned PDF download URL if the report has a PDF.
    pdf_url = None
    if pdf_r2_key and report.status in ("complete", "partial"):
        bucket = os.environ.get("CLOUDFLARE_R2_BUCKET_REPORTS", "")
        if bucket:
            pdf_url = generate_presigned_read_url(bucket, pdf_r2_key, expiry_seconds=900)

    return ReportDetailResponse(
        **report.model_dump(),
        sections=sections,
        pdf_url=pdf_url,
    )
