"""
Seed the Florida Rebels roster into Neon dev.

Mirrors scripts/seed_bbe_roster.py. Follows the same idempotent DELETE + INSERT
pattern. Roster sourced from the public Florida Rebels 17U roster page
(screenshot, April 2026). Run once to seed, re-run to update.

Requires:
  1. A Florida Rebels team row to exist in the `teams` table (create via /admin
     or a migration — don't hand-insert here). Set TEAM_ID below to that row's
     UUID before running.
  2. NEON_HOST, NEON_DB, NEON_USER, NEON_PASSWORD in backend/.env.

Usage:
    python scripts/seed_rebels_roster.py

Status: READY. TEAM_ID and ROSTER populated. Run to seed.
"""

import os
import sys

import psycopg2

# ==== FILL IN BEFORE RUNNING =================================================

# The Florida Rebels team_id from the `teams` table. Obtain by inserting the
# team row via /admin (or a migration) first, then paste the UUID here.
TEAM_ID: str | None = "b6710f8b-4b1a-4272-96f2-d5892ab3418e"  # Florida Rebels

USER_ID = "933c00c7-df54-43a4-ae2d-f36502347cce"  # Tommy / admin

# Source: Florida Rebels 17U public roster page (screenshot, April 2026).
# Position mapping from roster sheet: G → PG, W → SF, F → PF.
# Refine position, dominant_hand, and role from film observations.
ROSTER: list[dict] = [
    {"jersey": "0",  "name": "Donovan Williams Jr.", "pos": "PG", "height": "6'3\"",  "grad_year": "2026", "hs": "Edgewater (FL)"},
    {"jersey": "1",  "name": "Landyn Colyer",        "pos": "SF", "height": "6'6\"",  "grad_year": "2026", "hs": "Overtime Elite"},
    {"jersey": "3",  "name": "Caden Daughtry",       "pos": "PG", "height": "6'1\"",  "grad_year": "2027", "hs": "Calvary Christian (FL)"},
    {"jersey": "4",  "name": "Samuel Hallas",        "pos": "SF", "height": "6'6\"",  "grad_year": "2026", "hs": "Calvary Christian (FL)"},
    {"jersey": "5",  "name": "Angelo Moton",         "pos": "SF", "height": "6'6\"",  "grad_year": "2026", "hs": "Leesburg (FL)"},
    {"jersey": "6",  "name": "Mike Broxton Jr",      "pos": "PF", "height": "6'10\"", "grad_year": "2026", "hs": "Gibbs (FL)"},
    {"jersey": "8",  "name": "Dhani Miller",         "pos": "PG", "height": "6'3\"",  "grad_year": "2026", "hs": "Montverde Academy (FL)"},
    {"jersey": "10", "name": "Michael Madueme",      "pos": "PG", "height": "6'5\"",  "grad_year": "2026", "hs": "Lake Highland Prep (FL)"},
    {"jersey": "21", "name": "Tyler Bright",         "pos": "PF", "height": "6'9\"",  "grad_year": "2026", "hs": "The Rock (FL)"},
    {"jersey": "22", "name": "Rhiaughn Ferguson",    "pos": "PF", "height": "6'8\"",  "grad_year": "2026", "hs": "Downey Christian (FL)"},
    {"jersey": "23", "name": "Jaxon Richardson",     "pos": "SF", "height": "6'6\"",  "grad_year": "2026", "hs": "Columbus (FL)"},
]

# =============================================================================

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


def preflight() -> None:
    if not TEAM_ID:
        print("ERROR: TEAM_ID is not set. Insert the Florida Rebels team row via")
        print("       /admin (or a migration) first, then paste the UUID at the")
        print("       top of this script.")
        sys.exit(1)
    if not ROSTER:
        print("ERROR: ROSTER is empty. Populate with the confirmed Florida Rebels")
        print("       roster (jersey, name, pos, height, grad_year, hs) before running.")
        sys.exit(1)
    for var in ("NEON_HOST", "NEON_DB", "NEON_USER", "NEON_PASSWORD"):
        if not os.environ.get(var):
            print(f"ERROR: {var} not set.")
            sys.exit(1)


def main():
    load_env()
    preflight()

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
            print(f"Deleted {cur.rowcount} existing rows.")

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
        print(f"\nSeeded {len(ROSTER)} players to Florida Rebels.")

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
