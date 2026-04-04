CREATE TABLE teams (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid        NOT NULL REFERENCES users(id),
  name             text        NOT NULL,
  level            text        NOT NULL DEFAULT 'unknown',
  stats_source_url text,
  deleted_at       timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_teams_user_id ON teams(user_id);
