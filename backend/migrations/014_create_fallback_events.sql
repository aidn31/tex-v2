CREATE TABLE fallback_events (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id        uuid        NOT NULL REFERENCES reports(id),
  section_type     text        NOT NULL,
  primary_provider text        NOT NULL,
  fallback_provider text       NOT NULL,
  error_reason     text        NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_fallback_events_report_id ON fallback_events(report_id);
CREATE INDEX idx_fallback_events_created_at ON fallback_events(created_at DESC);
