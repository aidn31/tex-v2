CREATE TABLE dead_letter_tasks (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name        text        NOT NULL,
  task_args        jsonb       NOT NULL,
  queue            text        NOT NULL,
  error_message    text        NOT NULL,
  error_traceback  text,
  retry_count      integer     NOT NULL,
  film_id          uuid,
  report_id        uuid,
  user_id          uuid,
  created_at       timestamptz NOT NULL DEFAULT now(),
  replayed_at      timestamptz,
  resolved_at      timestamptz
);

CREATE INDEX idx_dead_letter_created_at ON dead_letter_tasks(created_at DESC);
CREATE INDEX idx_dead_letter_task_name ON dead_letter_tasks(task_name);
CREATE INDEX idx_dead_letter_user_id ON dead_letter_tasks(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_dead_letter_unresolved ON dead_letter_tasks(created_at)
  WHERE resolved_at IS NULL;
