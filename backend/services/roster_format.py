"""Roster formatting for Gemini context.

Produces the string format documented in PROMPTS.md CONTEXT STRUCTURE — SECTIONS 1-4:

    #3 Marcus Williams, PG, 6'2", primary_initiator, right-handed
    #10 Jordan Hayes, SF, 6'5", spacer
    ...
"""

from services.db import get_connection


def format_roster_for_prompt(team_id: str) -> str:
    """Fetch a team's roster from Neon and return the formatted context string.

    Empty roster returns '(no roster data available)' so the prompt still
    has a known placeholder instead of a blank section.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT jersey_number, full_name, position, height, role, dominant_hand "
                "FROM roster_players "
                "WHERE team_id = %s AND deleted_at IS NULL "
                "ORDER BY jersey_number",
                (team_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return "(no roster data available)"

    lines = []
    for jersey, full_name, position, height, role, hand in rows:
        parts = [f"#{jersey} {full_name}"]
        if position:
            parts.append(position)
        if height:
            parts.append(height)
        if role:
            parts.append(role)
        if hand:
            parts.append(f"{hand}-handed")
        lines.append(", ".join(parts))

    return "\n".join(lines)
