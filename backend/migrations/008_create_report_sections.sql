CREATE TABLE report_sections (
  id                       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id                uuid        NOT NULL REFERENCES reports(id),
  section_type             text        NOT NULL,
  status                   text        NOT NULL DEFAULT 'pending',
  content                  text,
  model_used               text,
  prompt_version           text        NOT NULL,
  chunk_count              integer,
  tokens_input             integer,
  tokens_output            integer,
  generation_time_seconds  integer,
  error_message            text,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  UNIQUE (report_id, section_type)
);

CREATE INDEX idx_report_sections_report_id ON report_sections(report_id);
CREATE INDEX idx_report_sections_status ON report_sections(status);
