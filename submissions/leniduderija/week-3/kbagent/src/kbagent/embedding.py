import os

from sentence_transformers import SentenceTransformer

from .models import Chunk

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        _model = SentenceTransformer(model_name)
    return _model


def _text_to_embed(chunk: Chunk) -> str:
    trail = " > ".join([chunk.path, *chunk.heading_trail])
    return f"{trail}\n\n{chunk.text}"


def embed_chunks(chunks: list[Chunk]):
    model = get_model()
    texts = [_text_to_embed(c) for c in chunks]
    return model.encode(texts, batch_size=64, show_progress_bar=True)
