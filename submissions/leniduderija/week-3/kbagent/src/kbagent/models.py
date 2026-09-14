from dataclasses import dataclass


@dataclass
class Shelf:
    id: int
    name: str
    slug: str
    description: str


@dataclass
class Book:
    id: int
    name: str
    slug: str
    description: str


@dataclass
class Chapter:
    id: int
    name: str
    slug: str
    description: str
    book_id: int


@dataclass
class Page:
    id: int
    name: str
    slug: str
    book_id: int
    chapter_id: int | None
    draft: bool
    template: bool
    created_at: str
    updated_at: str


@dataclass
class PageRecord:
    id: int
    name: str
    slug: str
    book_id: int
    chapter_id: int | None
    path: str
    shelf_names: list[str]
    markdown: str
    created_at: str
    updated_at: str
    url: str


@dataclass
class Chunk:
    page_id: int
    chunk_index: int
    path: str
    heading_trail: list[str]
    text: str
    url: str


@dataclass
class RetrievalResult:
    path: str
    heading_trail: list[str]
    url: str
    text: str
    distance: float
