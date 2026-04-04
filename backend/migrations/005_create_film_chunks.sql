CREATE TABLE film_chunks (
  id                     uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  film_id                uuid        NOT NULL REFERENCES films(id),
  chunk_index            integer     NOT NULL,
  duration_seconds       integer     NOT NULL,
  r2_chunk_key           text        NOT NULL,
  gemini_file_uri        text,
  gemini_file_state      text        NOT NULL DEFAULT 'uploading',
  gemini_file_expires_at timestamptz,
  created_at             timestamptz NOT NULL DEFAULT now(),
  UNIQUE (film_id, chunk_index)
);

CREATE INDEX idx_film_chunks_film_id ON film_chunks(film_id);
CREATE INDEX idx_film_chunks_expiry ON film_chunks(gemini_file_expires_at)
  WHERE gemini_file_state = 'active';
