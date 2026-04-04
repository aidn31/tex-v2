import os

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    FilmResponse,
    FilmUploadComplete,
    FilmUploadInitiate,
    FilmUploadInitiateResponse,
)
from services.clerk import get_current_user
from services.db import get_connection
from services.r2 import generate_presigned_upload_url

router = APIRouter()

FILM_COLUMNS = (
    "id, team_id, file_name, file_size_bytes, status, "
    "duration_seconds, chunk_count, error_message, created_at, updated_at"
)


def _row_to_response(row) -> FilmResponse:
    return FilmResponse(
        id=str(row[0]), team_id=str(row[1]), file_name=row[2],
        file_size_bytes=row[3], status=row[4], duration_seconds=row[5],
        chunk_count=row[6], error_message=row[7],
        created_at=row[8], updated_at=row[9],
    )


@router.post("/upload-initiate", response_model=FilmUploadInitiateResponse, status_code=201)
async def upload_initiate(
    body: FilmUploadInitiate, user: dict = Depends(get_current_user)
):
    user_id = str(user["id"])

    # Verify team belongs to user
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM teams WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (body.team_id, user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Team not found")

            # Create film row
            r2_key = f"films/{user_id}/{body.team_id}/{body.file_name}"
            cur.execute(
                "INSERT INTO films (user_id, team_id, file_name, file_size_bytes, r2_key) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, body.team_id, body.file_name, body.file_size_bytes, r2_key),
            )
            film_id = str(cur.fetchone()[0])

        conn.commit()
    finally:
        conn.close()

    # Generate presigned upload URL (1 hour expiry)
    bucket = os.environ["CLOUDFLARE_R2_BUCKET_FILMS"]
    # Use film_id in key to guarantee uniqueness
    r2_key = f"films/{user_id}/{film_id}/{body.file_name}"

    # Update r2_key with the film_id-based key
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE films SET r2_key = %s WHERE id = %s AND user_id = %s",
                (r2_key, film_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()

    upload_url = generate_presigned_upload_url(bucket, r2_key)

    return FilmUploadInitiateResponse(film_id=film_id, upload_url=upload_url)


@router.post("/upload-complete", response_model=FilmResponse)
async def upload_complete(
    body: FilmUploadComplete, user: dict = Depends(get_current_user)
):
    user_id = str(user["id"])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE films SET status = 'uploaded', updated_at = now() "
                f"WHERE id = %s AND user_id = %s AND status = 'uploaded' AND deleted_at IS NULL "
                f"RETURNING {FILM_COLUMNS}",
                (body.film_id, user_id),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Film not found")

    # Enqueue film processing
    from tasks.film_processing import process_film
    process_film.delay(str(row[0]))

    return _row_to_response(row)


@router.post("/upload-abort", status_code=204)
async def upload_abort(
    body: FilmUploadComplete, user: dict = Depends(get_current_user)
):
    user_id = str(user["id"])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE films SET deleted_at = now(), updated_at = now() "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (body.film_id, user_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Film not found")
        conn.commit()
    finally:
        conn.close()


@router.get("/", response_model=list[FilmResponse])
async def list_films(user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {FILM_COLUMNS} FROM films "
                "WHERE user_id = %s AND deleted_at IS NULL "
                "ORDER BY created_at DESC LIMIT 20",
                (str(user["id"]),),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [_row_to_response(r) for r in rows]


@router.post("/{film_id}/retry", response_model=FilmResponse)
async def retry_film(film_id: str, user: dict = Depends(get_current_user)):
    user_id = str(user["id"])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE films SET status = 'uploaded', error_message = NULL, updated_at = now() "
                f"WHERE id = %s AND user_id = %s AND status = 'error' AND deleted_at IS NULL "
                f"RETURNING {FILM_COLUMNS}",
                (film_id, user_id),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Film not found or not in error state")

    from tasks.film_processing import process_film
    process_film.delay(str(row[0]))

    return _row_to_response(row)


@router.get("/{film_id}", response_model=FilmResponse)
async def get_film(film_id: str, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {FILM_COLUMNS} FROM films "
                "WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (film_id, str(user["id"])),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Film not found")

    return _row_to_response(row)
