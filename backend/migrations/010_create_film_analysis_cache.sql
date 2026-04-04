CREATE TABLE film_analysis_cache (
  id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  file_hash          text        NOT NULL UNIQUE,
  film_id            uuid        REFERENCES films(id),
  sections           jsonb       NOT NULL,
  synthesis_document text,
  prompt_version     text        NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_film_cache_hash ON film_analysis_cache(file_hash);
CREATE INDEX idx_film_cache_prompt_version ON film_analysis_cache(prompt_version);
