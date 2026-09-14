import html
import re

from .constants import CHUNK_OVERLAP_CHARS, CHUNK_SIZE_CHARS
from .models import Chunk, PageRecord

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")

BOILERPLATE_PATTERNS = [
    re.compile(r"Feel free to send us any comments.*?bookstack@q\.agency\.?", re.IGNORECASE),
]


def _clean_text(text: str) -> str:
    stripped_text = html.unescape(re.sub(r"<[^>]+>", "", text))

    for pattern in BOILERPLATE_PATTERNS:
        stripped_text = pattern.sub("", stripped_text)

    return stripped_text


def _split_into_sections(markdown: str) -> list[dict]:
    lines = markdown.splitlines()

    if lines and HEADING_RE.match(lines[0]):
        lines = lines[1:]

    sections = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []

    def flush():
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                {
                    "heading_trail": [text for _, text in heading_stack],
                    "text": text,
                }
            )

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            flush()
            current_lines = []
            level = len(match.group(1))
            heading_text = _clean_text(match.group(2)).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading_text))
        else:
            current_lines.append(line)

    flush()
    return sections


def _split_oversized(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para

        if len(candidate) <= CHUNK_SIZE_CHARS:
            current = candidate
            continue

        # candidate overflows — first, flush whatever we'd accumulated
        overlap = ""
        if current:
            chunks.append(current)
            overlap = current[-CHUNK_OVERLAP_CHARS:]
            current = ""

        # then, independently, check whether *this paragraph itself*
        # (now leading the next chunk, with overlap prefixed) still fits
        candidate_alone = f"{overlap}\n\n{para}" if overlap else para
        if len(candidate_alone) <= CHUNK_SIZE_CHARS:
            current = candidate_alone
        else:
            # too big even on its own — nothing to pack it with, so
            # hard-split by character count (overlap dropped here: we're
            # already cutting mid-content with no natural boundary)
            for i in range(0, len(para), CHUNK_SIZE_CHARS):
                chunks.append(para[i : i + CHUNK_SIZE_CHARS])

    if current:
        chunks.append(current)

    return chunks


def chunk_page(record: PageRecord) -> list[Chunk]:
    sections = _split_into_sections(record.markdown)

    chunks = []
    for section in sections:
        text = _clean_text(section["text"])
        pieces = [text] if len(text) <= CHUNK_SIZE_CHARS else _split_oversized(text)

        for piece in pieces:
            chunks.append(
                Chunk(
                    page_id=record.id,
                    chunk_index=len(chunks),
                    path=record.path,
                    heading_trail=section["heading_trail"],
                    text=piece,
                    url=record.url,
                )
            )

    return chunks
