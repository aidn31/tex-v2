CREATE TABLE users (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id            text        NOT NULL UNIQUE,
  email               text        NOT NULL,
  is_admin            boolean     NOT NULL DEFAULT false,
  reports_used        integer     NOT NULL DEFAULT 0,
  report_credits      integer     NOT NULL DEFAULT 0,
  stripe_customer_id  text,
  deleted_at          timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_users_clerk_id ON users(clerk_id);
CREATE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;
