"""
Seed the Brad Beal Elite (EYBL) roster into Neon dev.

Wipes the 2 placeholder rows currently on that team and inserts the 9 players
pulled from the Brad Beal Elite public roster page. Defaults are applied for
fields the roster sheet does not provide (dominant_hand = 'right', role =
'role_player'). Tommy updates those as film-based observations come in.

Idempotent: running twice produces the same result. Uses DELETE + INSERT
(not UPSERT) because UNIQUE (team_id, jersey_number) blocks re-inserts
against soft-deleted rows and these placeholder rows have no downstream
FKs (reports/corrections reference film_id, not roster_player_id).

Usage:
    python scripts/seed_bbe_roster.py

Requires NEON_HOST, NEON_DB, NEON_USER, NEON_PASSWORD in backend/.env.
"""

import os
import sys

import psycopg2

TEAM_ID = "9585d9cd-e330-425b-97ea-b6628adfcac3"
USER_ID = "933c00c7-df54-43a4-ae2d-f36502347cce"

# Source: Brad Beal Elite 17U roster page (public), screenshot provided by Tommy.
# position mapping: G -> PG (default, update after film), W -> SF, F -> PF.
# dominant_hand and role are defaults; update from film observations.
ROSTER = [
    {"jersey": "1",  "name": "Quentin Coleman",  "pos": "PG", "height": "6'3\"",  "grad_year": "2026", "hs": "Principia (MO)"},
    {"jersey": "2",  "name": "Trey Pearson",     "pos": "PG", "height": "6'3\"",  "grad_year": "2026", "hs": "Pope John Paul II"},
    {"jersey": "5",  "name": "Cam Blivens",      "pos": "PG", "height": "6'2\"",  "grad_year": "2026", "hs": "Lipscomb Academy"},
    {"jersey": "10", "name": "Ty Edwards",       "pos": "PG", "height": "6'5\"",  "grad_year": "2026", "hs": "Cape Central"},
    {"jersey": "22", "name": "Jamison White",    "pos": "PF", "height": "6'9\"",  "grad_year": "2026", "hs": "Chaminade (MO)"},
    {"jersey": "23", "name": "JJ Andrews",       "pos": "SF", "height": "6'7\"",  "grad_year": "2026", "hs": "Little Rock Christian (AR)"},
    {"jersey": "31", "name": "Sheek Pearson",    "pos": "PF", "height": "6'11\"", "grad_year": "2026", "hs": "John Burroughs (MO)"},
    {"jersey": "32", "name": "Jaylan Mitchell",  "pos": "PF", "height": "6'8\"",  "grad_year": "2027", "hs": "FJ Reitz"},
    {"jersey": "33", "name": "Jahadi White",     "pos": "PF", "height": "6'8\"",  "grad_year": "2026", "hs": "Chaminade (MO)"},
]

DEFAULT_HAND = "right"
DEFAULT_ROLE = "role_player"


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    for var in ("NEON_HOST", "NEON_DB", "NEON_USER", "NEON_PASSWORD"):
        if not os.environ.get(var):
            print(f"ERROR: {var} not set.")
            sys.exit(1)

    conn = psycopg2.connect(
        host=os.environ["NEON_HOST"],
        database=os.environ["NEON_DB"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
        connect_timeout=10,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM teams WHERE id = %s AND deleted_at IS NULL;",
                (TEAM_ID,),
            )
            row = cur.fetchone()
            if not row:
                print(f"ERROR: team {TEAM_ID} not found or soft-deleted.")
                sys.exit(1)
            print(f"Target team: {row[0]} ({TEAM_ID})")

            cur.execute(
                "SELECT jersey_number, full_name FROM roster_players "
                "WHERE team_id = %s ORDER BY jersey_number;",
                (TEAM_ID,),
            )
            existing = cur.fetchall()
            print(f"Existing roster rows: {len(existing)}")
            for r in existing:
                print(f"  #{r[0]}: {r[1]}")

            cur.execute(
                "DELETE FROM roster_players WHERE team_id = %s;",
                (TEAM_ID,),
            )
            print(f"Deleted {cur.rowcount} placeholder rows.")

            insert_sql = """
                INSERT INTO roster_players
                    (user_id, team_id, jersey_number, full_name, position,
                     height, dominant_hand, role, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            for p in ROSTER:
                notes = f"{p['grad_year']} | {p['hs']}"
                cur.execute(
                    insert_sql,
                    (
                        USER_ID,
                        TEAM_ID,
                        p["jersey"],
                        p["name"],
                        p["pos"],
                        p["height"],
                        DEFAULT_HAND,
                        DEFAULT_ROLE,
                        notes,
                    ),
                )
                print(f"  Inserted #{p['jersey']:>2} {p['name']:<20} {p['pos']} {p['height']}")

        conn.commit()
        print(f"\nSeeded {len(ROSTER)} players to Brad Beal Elite.")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT jersey_number, full_name, position, height, dominant_hand, role "
                "FROM roster_players WHERE team_id = %s "
                "ORDER BY CAST(jersey_number AS integer);",
                (TEAM_ID,),
            )
            print("\nFinal roster in DB:")
            print("  # | Name                 | Pos | Ht     | Hand  | Role")
            print("  --|----------------------|-----|--------|-------|------------")
            for r in cur.fetchall():
                print(f"  {r[0]:>2} | {r[1]:<20} | {r[2]:<3} | {r[3]:<6} | {r[4]:<5} | {r[5]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
