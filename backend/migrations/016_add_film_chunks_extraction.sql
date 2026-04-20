-- Adds Prompt 0A (chunk extraction) output fields to film_chunks.
-- extract_chunk writes extraction_output after running Prompt 0A against the
-- chunk's Gemini file URI. run_chunk_synthesis reads these rows to build the
-- input for Prompt 0B.
--
-- extraction_status values: 'pending' | 'extracting' | 'complete' | 'error'.
-- Matches existing film_chunks.gemini_file_state style (unconstrained text).

ALTER TABLE film_chunks
  ADD COLUMN extraction_output text,
  ADD COLUMN extraction_status text NOT NULL DEFAULT 'pending';

CREATE INDEX idx_film_chunks_extraction_status ON film_chunks(film_id, extraction_status);
