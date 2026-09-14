from pathlib import Path

from .bookstack import BookStackClient
from .cache import crawl_and_cache
from .chunking import chunk_page
from .db import get_connection, init_schema
from .embedding import embed_chunks
from .models import PageRecord


def build_index(client: BookStackClient, cache_path: Path) -> None:
    records: list[PageRecord] = crawl_and_cache(client, cache_path)

    chunks = []
    for record in records:
        chunks.extend(chunk_page(record))
    print(f"[index] {len(chunks)} chunks from {len(records)} pages")

    embeddings = embed_chunks(chunks)
    print(f"[index] embedded {len(embeddings)} chunks")

    conn = get_connection()
    init_schema(conn)
    conn.execute("TRUNCATE chunks")

    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO chunks (page_id, chunk_index, path, heading_trail, url, text, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    chunk.page_id,
                    chunk.chunk_index,
                    chunk.path,
                    chunk.heading_trail,
                    chunk.url,
                    chunk.text,
                    embedding,
                ),
            )

    conn.commit()
    conn.close()
    print(f"[index] wrote {len(chunks)} chunks to pgvector")
