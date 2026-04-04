CREATE TABLE corrections (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id       uuid        NOT NULL REFERENCES reports(id),
  film_id         uuid        NOT NULL REFERENCES films(id),
  section_type    text        NOT NULL,
  phase           integer     NOT NULL DEFAULT 1,
  ai_claim        text        NOT NULL,
  is_correct      boolean     NOT NULL,
  correct_claim   text,
  category        text        NOT NULL,
  game_count      integer,
  confidence      text        NOT NULL DEFAULT 'high',
  prompt_version  text        NOT NULL,
  admin_notes     text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_corrections_report_id ON corrections(report_id);
CREATE INDEX idx_corrections_film_id ON corrections(film_id);
CREATE INDEX idx_corrections_category ON corrections(category);
CREATE INDEX idx_corrections_prompt_version ON corrections(prompt_version);
CREATE INDEX idx_corrections_section_type ON corrections(section_type);
CREATE INDEX idx_corrections_is_correct ON corrections(is_correct);
