"""Admin routes — all gated by require_admin on every request.

Per CLAUDE.md:
  - Check is_admin on every admin request, not just at login
  - Only the service role key can insert into corrections
  - corrections table is the training dataset — never soft-deleted
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.clerk import require_admin
from services.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CorrectionCreate(BaseModel):
    report_id: str
    film_id: str
    section_type: str
    ai_claim: str
    is_correct: bool
    correct_claim: Optional[str] = None
    category: str
    confidence: str = "high"
    prompt_version: str
    admin_notes: Optional[str] = None


class CreditGrant(BaseModel):
    credits: int


# ---------------------------------------------------------------------------
# 4.2 — GET /admin/corrections
# ---------------------------------------------------------------------------

@router.get("/corrections")
async def list_corrections(
    section_type: Optional[str] = Query(None),
    prompt_version: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_correct: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    user: dict = Depends(require_admin),
):
    """List corrections, filterable by section, version, category, correctness."""
    conditions = []
    params: list = []

    if section_type:
        conditions.append("section_type = %s")
        params.append(section_type)
    if prompt_version:
        conditions.append("prompt_version = %s")
        params.append(prompt_version)
    if category:
        conditions.append("category = %s")
        params.append(category)
    if is_correct is not None:
        conditions.append("is_correct = %s")
        params.append(is_correct)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, report_id, film_id, section_type, ai_claim, "
                f"is_correct, correct_claim, category, confidence, "
                f"prompt_version, admin_notes, created_at "
                f"FROM corrections {where} "
                f"ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) FROM corrections {where}", params)
            total = cur.fetchone()[0]
    finally:
        conn.close()

    return {
        "corrections": [
            {
                "id": str(r[0]),
                "report_id": str(r[1]),
                "film_id": str(r[2]),
                "section_type": r[3],
                "ai_claim": r[4],
                "is_correct": r[5],
                "correct_claim": r[6],
                "category": r[7],
                "confidence": r[8],
                "prompt_version": r[9],
                "admin_notes": r[10],
                "created_at": r[11].isoformat() if r[11] else None,
            }
            for r in rows
        ],
        "total": total,
    }


# ---------------------------------------------------------------------------
# 4.3 — POST /admin/corrections
# ---------------------------------------------------------------------------

VALID_SECTION_TYPES = {
    "offensive_sets", "defensive_schemes", "pnr_coverage",
    "player_pages", "game_plan", "adjustments_practice",
}
VALID_CATEGORIES = {
    "set_identification", "player_attribution", "frequency_count",
    "tendency", "coverage_type", "personnel_evaluation",
    "strategic_reasoning",
}
VALID_CONFIDENCE = {"high", "medium", "low"}


@router.post("/corrections", status_code=201)
async def create_correction(
    body: CorrectionCreate,
    user: dict = Depends(require_admin),
):
    """Save a correction for a specific AI claim in a report section."""
    if body.section_type not in VALID_SECTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid section_type: {body.section_type}")
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {body.category}")
    if body.confidence not in VALID_CONFIDENCE:
        raise HTTPException(status_code=400, detail=f"Invalid confidence: {body.confidence}")
    if not body.is_correct and not body.correct_claim:
        raise HTTPException(status_code=400, detail="correct_claim is required when is_correct is false")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verify report and film exist
            cur.execute("SELECT id FROM reports WHERE id = %s", (body.report_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Report not found")
            cur.execute("SELECT id FROM films WHERE id = %s", (body.film_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Film not found")

            cur.execute(
                "INSERT INTO corrections "
                "(report_id, film_id, section_type, ai_claim, is_correct, "
                "correct_claim, category, confidence, prompt_version, admin_notes) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "RETURNING id",
                (
                    body.report_id,
                    body.film_id,
                    body.section_type,
                    body.ai_claim,
                    body.is_correct,
                    body.correct_claim,
                    body.category,
                    body.confidence,
                    body.prompt_version,
                    body.admin_notes,
                ),
            )
            correction_id = str(cur.fetchone()[0])
        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Correction saved",
        extra={
            "correction_id": correction_id,
            "report_id": body.report_id,
            "section_type": body.section_type,
            "is_correct": body.is_correct,
            "category": body.category,
        },
    )
    return {"id": correction_id}


# ---------------------------------------------------------------------------
# 4.4 — GET /admin/pattern-analysis
# ---------------------------------------------------------------------------

@router.get("/pattern-analysis")
async def pattern_analysis(
    prompt_version: Optional[str] = Query(None),
    user: dict = Depends(require_admin),
):
    """Error rate by category and section type for a given prompt version.

    Returns aggregated stats showing where the AI is making mistakes,
    so Tommy knows which prompts to improve.
    """
    version_filter = ""
    params: list = []
    if prompt_version:
        version_filter = "WHERE prompt_version = %s"
        params.append(prompt_version)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Error rate by category
            cur.execute(
                f"SELECT category, "
                f"COUNT(*) as total, "
                f"SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END) as errors, "
                f"ROUND(100.0 * SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END) / "
                f"NULLIF(COUNT(*), 0), 1) as error_rate "
                f"FROM corrections {version_filter} "
                f"GROUP BY category ORDER BY error_rate DESC NULLS LAST",
                params,
            )
            by_category = [
                {
                    "category": r[0],
                    "total": r[1],
                    "errors": r[2],
                    "error_rate": float(r[3]) if r[3] else 0,
                }
                for r in cur.fetchall()
            ]

            # Error rate by section type
            cur.execute(
                f"SELECT section_type, "
                f"COUNT(*) as total, "
                f"SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END) as errors, "
                f"ROUND(100.0 * SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END) / "
                f"NULLIF(COUNT(*), 0), 1) as error_rate "
                f"FROM corrections {version_filter} "
                f"GROUP BY section_type ORDER BY error_rate DESC NULLS LAST",
                params,
            )
            by_section = [
                {
                    "section_type": r[0],
                    "total": r[1],
                    "errors": r[2],
                    "error_rate": float(r[3]) if r[3] else 0,
                }
                for r in cur.fetchall()
            ]

            # Overall stats
            cur.execute(
                f"SELECT COUNT(*), "
                f"SUM(CASE WHEN is_correct = false THEN 1 ELSE 0 END), "
                f"COUNT(DISTINCT prompt_version) "
                f"FROM corrections {version_filter}",
                params,
            )
            overall = cur.fetchone()

            # Available prompt versions
            cur.execute(
                "SELECT DISTINCT prompt_version FROM corrections "
                "ORDER BY prompt_version DESC"
            )
            versions = [r[0] for r in cur.fetchall()]

    finally:
        conn.close()

    return {
        "by_category": by_category,
        "by_section": by_section,
        "total_corrections": overall[0] or 0,
        "total_errors": overall[1] or 0,
        "prompt_versions_reviewed": overall[2] or 0,
        "available_versions": versions,
    }


# ---------------------------------------------------------------------------
# 4.5 — GET /admin/users
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(user: dict = Depends(require_admin)):
    """List all coaches with report counts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT u.id, u.email, u.is_admin, u.reports_used, "
                "u.report_credits, u.created_at, "
                "(SELECT COUNT(*) FROM reports r WHERE r.user_id = u.id "
                " AND r.deleted_at IS NULL) as report_count "
                "FROM users u WHERE u.deleted_at IS NULL "
                "ORDER BY u.created_at DESC"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": str(r[0]),
            "email": r[1],
            "is_admin": r[2],
            "reports_used": r[3],
            "report_credits": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "report_count": r[6],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 4.6 — POST /admin/users/{id}/credits
# ---------------------------------------------------------------------------

@router.post("/users/{user_id}/credits")
async def grant_credits(
    user_id: str,
    body: CreditGrant,
    user: dict = Depends(require_admin),
):
    """Manually grant report credits to a coach."""
    if body.credits < 1:
        raise HTTPException(status_code=400, detail="Credits must be at least 1")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET report_credits = report_credits + %s, "
                "updated_at = now() WHERE id = %s AND deleted_at IS NULL "
                "RETURNING report_credits",
                (body.credits, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Credits granted",
        extra={
            "target_user_id": user_id,
            "credits_granted": body.credits,
            "new_balance": row[0],
            "admin_id": str(user["id"]),
        },
    )
    return {"user_id": user_id, "credits_granted": body.credits, "new_balance": row[0]}
