import time

import requests

from .errors import BookStackAPIError
from .models import Book, Chapter, Page, PageRecord, Shelf


class BookStackClient:
    PAGE_SIZE = 500
    REQUEST_DELAY_SECONDS = 0.35
    MAX_RATE_LIMIT_RETRIES = 5

    def __init__(self, base_url, token_id, token_secret, timeout=15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Token {token_id}:{token_secret}"

    def _get(self, path, params=None):
        url = f"{self.base_url}{path}"
        for attempt in range(self.MAX_RATE_LIMIT_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.exceptions.RequestException as e:
                raise BookStackAPIError(f"GET {path} failed: {e}") from e

            if response.status_code == 429:
                time.sleep(2**attempt)
                continue

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise BookStackAPIError(f"GET {path} failed: {e}") from e

            time.sleep(self.REQUEST_DELAY_SECONDS)
            return response

        raise BookStackAPIError(f"GET {path} failed after repeated 429 rate-limit responses")

    def _list_all(self, path):
        results = []
        offset = 0
        while True:
            body = self._get(path, params={"count": self.PAGE_SIZE, "offset": offset}).json()
            results.extend(body["data"])
            offset += self.PAGE_SIZE
            if offset >= body["total"]:
                break
        return results

    def list_shelves(self):
        return [
            Shelf(id=s["id"], name=s["name"], slug=s["slug"], description=s.get("description", ""))
            for s in self._list_all("/api/shelves")
        ]

    def get_shelf_book_ids(self, shelf_id):
        detail = self._get(f"/api/shelves/{shelf_id}").json()
        return [b["id"] for b in detail.get("books", [])]

    def list_books(self):
        return [
            Book(id=b["id"], name=b["name"], slug=b["slug"], description=b.get("description", ""))
            for b in self._list_all("/api/books")
        ]

    def list_chapters(self):
        return [
            Chapter(
                id=c["id"],
                name=c["name"],
                slug=c["slug"],
                description=c.get("description", ""),
                book_id=c["book_id"],
            )
            for c in self._list_all("/api/chapters")
        ]

    def list_pages(self):
        return [
            Page(
                id=p["id"],
                name=p["name"],
                slug=p["slug"],
                book_id=p["book_id"],
                chapter_id=p.get("chapter_id") or None,
                draft=p.get("draft", False),
                template=p.get("template", False),
                created_at=p.get("created_at", ""),
                updated_at=p.get("updated_at", ""),
            )
            for p in self._list_all("/api/pages")
        ]

    def get_page_markdown(self, page_id):
        return self._get(f"/api/pages/{page_id}/export/markdown").text


def crawl(client: BookStackClient, cached_pages: dict[int, dict] | None = None) -> list[PageRecord]:
    """Crawl BookStack into a list of PageRecords.

    `cached_pages` is an optional {page_id: {"updated_at": ..., "markdown": ...}}
    map from a previous run (see cache.load_cache) — a page whose `updated_at`
    matches the cached value reuses the cached markdown instead of re-fetching
    it, which is the expensive per-page request.
    """
    cached_pages = cached_pages or {}

    shelves = client.list_shelves()
    print(f"[crawl] {len(shelves)} shelves — resolving shelf-to-book membership...")
    book_id_to_shelf_names: dict[int, list[str]] = {}
    for shelf in shelves:
        for book_id in client.get_shelf_book_ids(shelf.id):
            book_id_to_shelf_names.setdefault(book_id, []).append(shelf.name)

    books_by_id = {b.id: b for b in client.list_books()}
    chapters_by_id = {c.id: c for c in client.list_chapters()}
    pages = client.list_pages()
    print(f"[crawl] {len(books_by_id)} books, {len(chapters_by_id)} chapters, {len(pages)} pages listed")

    records = []
    skipped = 0
    reused = 0
    refetched = 0
    for i, page in enumerate(pages, start=1):
        if page.draft or page.template:
            skipped += 1
            continue

        book = books_by_id.get(page.book_id)
        chapter = chapters_by_id.get(page.chapter_id) if page.chapter_id else None

        path_parts = [book.name if book else f"book:{page.book_id}"]
        if chapter:
            path_parts.append(chapter.name)
        path_parts.append(page.name)

        cached = cached_pages.get(page.id)
        if cached and cached.get("updated_at") == page.updated_at:
            markdown = cached["markdown"]
            reused += 1
        else:
            markdown = client.get_page_markdown(page.id)
            refetched += 1

        if (reused + refetched) % 25 == 0 or i == len(pages):
            print(
                f"[crawl] processed {i}/{len(pages)} "
                f"({reused} reused from cache, {refetched} refetched, {skipped} skipped)..."
            )

        records.append(
            PageRecord(
                id=page.id,
                name=page.name,
                slug=page.slug,
                book_id=page.book_id,
                chapter_id=page.chapter_id,
                path=" > ".join(path_parts),
                shelf_names=book_id_to_shelf_names.get(page.book_id, []),
                markdown=markdown,
                created_at=page.created_at,
                updated_at=page.updated_at,
                url=f"{client.base_url}/books/{book.slug if book else page.book_id}/page/{page.slug}",
            )
        )

    print(
        f"[crawl] done: {len(records)} pages ingested "
        f"({reused} reused from cache, {refetched} refetched, {skipped} draft/template skipped)"
    )
    return records
