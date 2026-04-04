CREATE TABLE payments (
  id                        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                   uuid        NOT NULL REFERENCES users(id),
  report_id                 uuid        REFERENCES reports(id),
  stripe_session_id         text        NOT NULL UNIQUE,
  stripe_payment_intent_id  text,
  amount_cents              integer     NOT NULL,
  currency                  text        NOT NULL DEFAULT 'usd',
  status                    text        NOT NULL DEFAULT 'pending',
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_stripe_session_id ON payments(stripe_session_id);
