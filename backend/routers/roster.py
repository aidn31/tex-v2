from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.errors import UniqueViolation

from models.schemas import RosterPlayerCreate, RosterPlayerResponse, RosterPlayerUpdate
from services.clerk import get_current_user
from services.db import get_connection

router = APIRouter()

PLAYER_COLUMNS = (
    "id, team_id, jersey_number, full_name, position, "
    "height, dominant_hand, role, notes, created_at, updated_at"
)


def _row_to_response(row) -> RosterPlayerResponse:
    return RosterPlayerResponse(
        id=str(row[0]), team_id=str(row[1]), jersey_number=row[2],
        full_name=row[3], position=row[4], height=row[5],
        dominant_hand=row[6], role=row[7], notes=row[8],
        created_at=row[9], updated_at=row[10],
    )


@router.post("/", response_model=RosterPlayerResponse, status_code=201)
async def create_player(
    body: RosterPlayerCreate, user: dict = Depends(get_current_user)
):
    # Verify the team belongs to this user
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM teams WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (body.team_id, str(user["id"])),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Team not found")

            try:
                cur.execute(
                    f"INSERT INTO roster_players "
                    f"(user_id, team_id, jersey_number, full_name, position, "
                    f"height, dominant_hand, role, notes) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    f"RETURNING {PLAYER_COLUMNS}",
                    (
                        str(user["id"]), body.team_id, body.jersey_number,
                        body.full_name, body.position, body.height,
                        body.dominant_hand, body.role, body.notes,
                    ),
                )
            except UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Jersey number {body.jersey_number} already exists on this team",
                )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return _row_to_response(row)


@router.get("/", response_model=list[RosterPlayerResponse])
async def list_players(
    team_id: str = Query(...), user: dict = Depends(get_current_user)
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {PLAYER_COLUMNS} FROM roster_players "
                "WHERE team_id = %s AND user_id = %s AND deleted_at IS NULL "
                "ORDER BY jersey_number",
                (team_id, str(user["id"])),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [_row_to_response(r) for r in rows]


@router.get("/{player_id}", response_model=RosterPlayerResponse)
async def get_player(player_id: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {PLAYER_COLUMNS} FROM roster_players "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (player_id, str(user["id"])),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")

    return _row_to_response(row)


@router.patch("/{player_id}", response_model=RosterPlayerResponse)
async def update_player(
    player_id: str, body: RosterPlayerUpdate, user: dict = Depends(get_current_user)
):
    updates = []
    values = []
    for field in ("jersey_number", "full_name", "position", "height", "dominant_hand", "role", "notes"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = %s")
            values.append(val)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = now()")
    values.extend([player_id, str(user["id"])])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    f"UPDATE roster_players SET {', '.join(updates)} "
                    f"WHERE id = %s AND user_id = %s AND deleted_at IS NULL "
                    f"RETURNING {PLAYER_COLUMNS}",
                    values,
                )
            except UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Jersey number already exists on this team",
                )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")

    return _row_to_response(row)


@router.delete("/{player_id}", status_code=204)
async def delete_player(player_id: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE roster_players SET deleted_at = now(), updated_at = now() "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (player_id, str(user["id"])),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Player not found")
        conn.commit()
    finally:
        conn.close()
