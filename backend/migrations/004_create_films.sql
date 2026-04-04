CREATE TABLE films (
  id                        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                   uuid        NOT NULL REFERENCES users(id),
  team_id                   uuid        NOT NULL REFERENCES teams(id),
  file_name                 text        NOT NULL,
  file_size_bytes           bigint      NOT NULL,
  r2_key                    text        NOT NULL,
  duration_seconds          integer,
  file_hash                 text,
  status                    text        NOT NULL DEFAULT 'uploaded',
  gemini_processing_status  text,
  chunk_count               integer,
  synthesis_failed          boolean     NOT NULL DEFAULT false,
  error_message             text,
  deleted_at                timestamptz,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_films_user_id ON films(user_id);
CREATE INDEX idx_films_team_id ON films(team_id);
CREATE INDEX idx_films_status ON films(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_films_file_hash ON films(file_hash) WHERE file_hash IS NOT NULL;
