from .constants import RETRIEVAL_QUERY_INSTRUCTION, RETRIEVAL_TOP_K
from .db import get_connection
from .embedding import get_model
from .models import RetrievalResult


def retrieve(query: str, k: int = RETRIEVAL_TOP_K) -> list[RetrievalResult]:
    model = get_model()
    query_embedding = model.encode(RETRIEVAL_QUERY_INSTRUCTION + query)

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT path, heading_trail, url, text, embedding <=> %s AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s
        """,
        (query_embedding, k),
    ).fetchall()
    conn.close()

    return [
        RetrievalResult(path=path, heading_trail=heading_trail, url=url, text=text, distance=distance)
        for path, heading_trail, url, text, distance in rows
    ]
