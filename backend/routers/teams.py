from fastapi import APIRouter, Depends, HTTPException

from models.schemas import TeamCreate, TeamResponse, TeamUpdate
from services.clerk import get_current_user
from services.db import get_connection

router = APIRouter()


@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(body: TeamCreate, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO teams (user_id, name, level) VALUES (%s, %s, %s) "
                "RETURNING id, name, level, created_at, updated_at",
                (str(user["id"]), body.name, body.level),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return TeamResponse(
        id=str(row[0]), name=row[1], level=row[2],
        created_at=row[3], updated_at=row[4],
    )


@router.get("/", response_model=list[TeamResponse])
async def list_teams(user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, level, created_at, updated_at "
                "FROM teams WHERE user_id = %s AND deleted_at IS NULL "
                "ORDER BY created_at DESC",
                (str(user["id"]),),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        TeamResponse(
            id=str(r[0]), name=r[1], level=r[2],
            created_at=r[3], updated_at=r[4],
        )
        for r in rows
    ]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, level, created_at, updated_at "
                "FROM teams WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (team_id, str(user["id"])),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamResponse(
        id=str(row[0]), name=row[1], level=row[2],
        created_at=row[3], updated_at=row[4],
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str, body: TeamUpdate, user: dict = Depends(get_current_user)
):
    updates = []
    values = []
    if body.name is not None:
        updates.append("name = %s")
        values.append(body.name)
    if body.level is not None:
        updates.append("level = %s")
        values.append(body.level)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = now()")
    values.extend([team_id, str(user["id"])])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE teams SET {', '.join(updates)} "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL "
                "RETURNING id, name, level, created_at, updated_at",
                values,
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamResponse(
        id=str(row[0]), name=row[1], level=row[2],
        created_at=row[3], updated_at=row[4],
    )


@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE teams SET deleted_at = now(), updated_at = now() "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (team_id, str(user["id"])),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Team not found")
        conn.commit()
    finally:
        conn.close()
