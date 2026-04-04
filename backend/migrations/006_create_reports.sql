CREATE TABLE reports (
  id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid        NOT NULL REFERENCES users(id),
  team_id                 uuid        NOT NULL REFERENCES teams(id),
  title                   text,
  report_type             text        NOT NULL DEFAULT 'opponent_scout',
  status                  text        NOT NULL DEFAULT 'pending',
  pdf_r2_key              text,
  context_cache_uri       text,
  prompt_version          text        NOT NULL,
  generation_time_seconds integer,
  error_message           text,
  completed_at            timestamptz,
  deleted_at              timestamptz,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_team_id ON reports(team_id);
CREATE INDEX idx_reports_status ON reports(status) WHERE deleted_at IS NULL;
