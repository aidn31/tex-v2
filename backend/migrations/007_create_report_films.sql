CREATE TABLE report_films (
  report_id  uuid NOT NULL REFERENCES reports(id),
  film_id    uuid NOT NULL REFERENCES films(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (report_id, film_id)
);

CREATE INDEX idx_report_films_film_id ON report_films(film_id);
