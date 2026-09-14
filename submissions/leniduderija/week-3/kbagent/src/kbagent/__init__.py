import os
from pathlib import Path

from dotenv import load_dotenv

from kbagent.bookstack import BookStackClient
from kbagent.pipeline import build_index

CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "kb_cache.jsonl"


def main() -> None:
    load_dotenv()

    client = BookStackClient(os.environ["KB_BASE_URL"], os.environ["KB_TOKEN_ID"], os.environ["KB_TOKEN_SECRET"])
    build_index(client, CACHE_PATH)