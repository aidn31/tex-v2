CREATE TABLE roster_players (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid        NOT NULL REFERENCES users(id),
  team_id          uuid        NOT NULL REFERENCES teams(id),
  jersey_number    text        NOT NULL,
  full_name        text        NOT NULL,
  position         text,
  height           text,
  dominant_hand    text,
  role             text,
  notes            text,
  deleted_at       timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (team_id, jersey_number)
);

CREATE INDEX idx_roster_players_user_id ON roster_players(user_id);
CREATE INDEX idx_roster_players_team_id ON roster_players(team_id);
