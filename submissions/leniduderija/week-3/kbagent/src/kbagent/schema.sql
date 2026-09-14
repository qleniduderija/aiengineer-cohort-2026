CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    path TEXT NOT NULL,
    heading_trail TEXT[] NOT NULL,
    url TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
