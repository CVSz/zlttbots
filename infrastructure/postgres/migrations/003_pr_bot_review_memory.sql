CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS review_memory (
  id BIGSERIAL PRIMARY KEY,
  repo TEXT NOT NULL,
  file TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL,
  issue TEXT NOT NULL,
  fix TEXT NOT NULL,
  severity TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS review_memory_embedding_ivfflat_idx
  ON review_memory USING ivfflat (embedding vector_cosine_ops);
