import dataclasses
import json
from pathlib import Path

from .bookstack import BookStackClient, crawl
from .models import PageRecord


def load_cache(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}

    cache = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            cache[record["id"]] = record
    return cache


def save_cache(path: Path, records: list[PageRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(dataclasses.asdict(record)) + "\n")


def crawl_and_cache(client: BookStackClient, cache_path: Path) -> list[PageRecord]:
    old_cache = load_cache(cache_path)
    print(f"[cache] loaded {len(old_cache)} pages from {cache_path}")

    records = crawl(client, cached_pages=old_cache)

    dropped = len(old_cache) - len({r.id for r in records} & set(old_cache))
    if dropped:
        print(f"[cache] {dropped} page(s) from the old cache no longer exist in BookStack — dropped")

    save_cache(cache_path, records)
    print(f"[cache] wrote {len(records)} pages to {cache_path}")
    return records
