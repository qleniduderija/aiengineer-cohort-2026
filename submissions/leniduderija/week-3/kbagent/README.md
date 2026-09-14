# kbagent

A RAG chat agent that answers questions about Q Agency's internal processes, policies, and technical standards — content is ingested from `kb.q.agency` (a BookStack instance) into pgvector, retrieved with a fixed retrieve→generate pipeline, and served through a basic web chat interface.

Built for Week 3 of the AI Engineer Cohort 2026, extending [Week 1's codebaseqa CLI](../../week-1/codebaseqa/) and [Week 2's extractstructdata CLI](../../week-2/extractstructdata/) — see those projects for the streaming-loop, cost-tracking, and error-handling patterns reused here.

## Data note

kb.q.agency is Q Agency's real internal knowledge base. The agent ingests it live via the BookStack API (see `bookstack.py`/`cache.py`) using the runner's own API token — nothing derived from it is committed to this public fork: the local JSONL cache (`data/`) and the pgvector database are both gitignored/local-only and regenerate on each run from a fresh crawl. The retrieval-eval question set (`eval/questions.*`, added in Phase 5) is committed with questions only; expected ground-truth answers are withheld and submitted separately, not pushed to this public repo.

## Setup

Requires VPN access to Q's internal network — both `kb.q.agency` (BookStack) and the course's Anthropic-compatible gateway (`API_ENDPOINT_BASE_URL`) are only reachable that way.

```bash
# 1. Start local Postgres + pgvector
docker compose up -d

# 2. Install dependencies
uv sync

# 3. Fill in .env (copy .env.example) — Anthropic/gateway creds, BookStack API token
#    (kb.q.agency profile > API Tokens), DATABASE_URL

# 4. Build the index: crawl kb.q.agency, chunk, embed, store in pgvector
#    (first run takes several minutes; later runs only re-fetch/re-embed changed pages)
uv run kbagent

# 5. Start the chat web UI
uv run kbagent-web
# -> open http://127.0.0.1:8000

# 6. (optional) Reproduce the retrieval-quality eval
uv run python -m kbagent.eval_score
```

## Architecture

Pipeline: `kbagent` crawls BookStack → chunks each page (`chunking.py`) → embeds chunks locally (`embedding.py`) → stores them in pgvector (`db.py`/`pipeline.py`). `kbagent-web` serves a chat UI that, per question, retrieves the top-k relevant chunks (`retrieval.py`) and asks Claude to answer using only that context (`chat.py`).

- **Retrieval:** fixed retrieve→generate pipeline (not agentic tool-use) — chosen so the required retrieval-quality evaluation has one deterministic retrieval step per question to score against ground truth. Revisited in Week 6 when hybrid search is introduced.
- **Re-indexing:** every `uv run kbagent` run truncates and rebuilds the `chunks` table from scratch (simple, not incremental) — a deliberate scope decision over a content-hash/ledger-based incremental update, since the corpus is small enough (a few minutes to re-embed) that the added complexity wasn't worth it here.
- **Single-user scope:** `kbagent-web` keeps one shared conversation/cost-total in memory for the whole process — fine for running locally by yourself, not built for multiple concurrent users (no per-visitor sessions).

## Retrieval quality evaluation

**Test set construction:** rather than hand-writing 30 questions from scratch, `eval_generate.py` samples one random chunk per distinct page (30 pages, across as many different books/topics as the corpus allows) and asks Claude — via forced tool-use, same pattern as week 2's structured extraction — to generate one natural question and answer grounded only in that passage. Because each question is generated *from* a specific known chunk, the source page it should retrieve is known by construction, with no manual labeling needed.

Two of the 30 generated questions were discarded on inspection — both were generated from a recurring boilerplate sentence ("where should I send feedback about this documentation") that our chunking cleanup pass didn't catch (a different phrasing than the one boilerplate pattern we specifically stripped). Testing retrieval against a boilerplate sentence isn't a meaningful test of retrieval quality, so those two were removed, leaving **28 questions** — still comfortably above the assignment's ≥20 minimum. (Worth noting as a real, if minor, chunking-cleanup gap: our boilerplate regex is pattern-specific, not exhaustive — see the chunking strategy's "known limitations.")

**Files:** `eval/questions.jsonl` (committed — `id`, `question`, `expected_source_path`) and `eval/answers.jsonl` (gitignored, not committed to this public fork — the generated ground-truth answer text is submitted separately, per this project's data-handling note above).

**Scoring (`eval_score.py`):** for each question, run it through the same `retrieve()` used by the live chat agent (top-`k`=5), and check whether `expected_source_path` appears anywhere in the results — matched at the **page level**, not exact chunk, since a chunk is an arbitrary slice of a page and requiring the literal chunk would be a stricter, less meaningful test than "did retrieval find the right source." Two metrics:
- **Hit rate @ top-5** — fraction of questions where the correct page appeared anywhere in the top 5 results.
- **MRR (Mean Reciprocal Rank)** — average of `1/rank` of the correct page (0 if absent from top-5) — rewards the right answer appearing *higher*, not just present.

**Results:**

| Metric | Value |
|---|---|
| Questions evaluated | 28 |
| Hit rate @ top-5 | **92.86%** (26/28) |
| MRR | **0.798** |

Most hits landed at rank 1 (the correct page was the single best match, not just "somewhere in the top 5"), which is a strong signal for the chunking + embedding design overall. The two misses were both broader "what needs to happen before X" / "who is responsible for X" process questions — the kind of question where the answer may be implied across a page's surrounding context rather than stated in one retrievable chunk, a plausible edge case for chunk-level retrieval regardless of the underlying model.

## Chunking strategy

**Approach: hierarchical/structure-aware chunking** — split primarily on the page's own markdown headings, with a size-bounded fallback for sections (or whole pages) too large or too flat to split structurally.

### What the data actually looks like

BookStack's hierarchy is Shelf → Book → Chapter → Page, but pages are where the actual content lives — shelves/books/chapters only contribute organizational metadata used to build each chunk's citation path. So the chunking analysis focuses on page content specifically. We pulled per-page markdown length (characters) across the whole corpus, then approximated token counts (~4 characters/token, a standard rule of thumb for English text) to reason about sizing in more familiar units, and didn't use a library like LlamaIndex or `unstructured` for the chunking itself — the strategy below is tailored to specifics of this data (BookStack's markdown export, leftover Confluence-migration HTML, a recurring boilerplate sentence) that a generic library wouldn't know to handle on its own.

- **673 pages** after filtering drafts/templates.
- **Page length: min 16 chars, median ~5,724 chars (≈1,400 tokens), p90 ~27,888 chars (≈7,000 tokens), max 315,430 chars (≈79,000 tokens).** The median alone is already 3-4x larger than a typical single-chunk target (200-500 tokens), so a single fixed-size chunk per page was never viable — nearly every page needs splitting. The long tail matters even more: some individual heading-delimited *sections* turned out to be tens of thousands of characters on their own (see the bug below), so the size-bound fallback has to work within a section, not just at the whole-page level.
- **~20% of pages (133/673) have no headings beyond their own auto-generated title.** Pure heading-based chunking can't be the whole strategy — a meaningful fifth of the corpus has nothing to split on structurally, so these "flat" pages need a fallback that works from raw prose alone (paragraph-packing up to the size cap).
- **Average ~6.5 real in-content headings per page** (excluding the auto-title). This is what justifies heading-splitting as the *primary* strategy rather than a nice-to-have — the other ~80% of pages have real structure to lean on, and splitting along it keeps semantically related content together instead of cutting arbitrarily.

### The algorithm

1. **Strip the page's auto-generated title heading.** BookStack's export always prepends the page's own name as an H1; that's redundant with the page path already captured separately as chunk metadata, so keeping it as content would waste space without adding information.
2. **Walk the document, tracking a heading-ancestor stack, splitting into sections at each heading boundary.** We track the *full* ancestor path (e.g. `["4. Standards", "4.1 Understanding the organization"]`), not just the nearest heading — a chunk's immediate heading alone can be ambiguous out of context ("4.1 Understanding the organization" means little without knowing it sits under "4. Standards"). The full trail is also what gets prefixed to chunk text before embedding, giving short/generic chunks more context to embed against.
3. **Size-bound each section.** Sections under the cap become one chunk as-is. Oversized sections (or flat pages with no real heading structure) get split further by packing paragraphs — split on blank lines, `"\n\n"` — up to the cap, with overlap carried into the next chunk. Paragraph-level packing beats naive fixed-character slicing because a paragraph is usually one coherent thought; cutting mid-paragraph loses more context than cutting between paragraphs. If a paragraph is still too large even alone, only then does it get a hard character-count split. Overlap applies *only* within this paragraph-packing fallback, between two chunks that came from the *same* oversized section — never across a heading boundary, since a new heading is already a real topic change and carrying old content across it would add noise, not continuity.
4. **A cleanup pass strips residual HTML artifacts and known boilerplate text before any sizing decision is made.** This has to run *before* the size check, not after — confirmed directly: one page's chunk count dropped from 10 to 8 once cleanup ran first, because leftover HTML markup (`<div class="fabric-editor-breakout-mark...">` and similar Confluence-migration artifacts) was inflating a section's raw character count without adding real content, triggering splits that weren't actually necessary.

### Parameter choices

- **Chunk size cap: 1,600 characters (~400 tokens).** Standard RAG guidance targets roughly 200-500 tokens per chunk. Since the median page is ~1,400 tokens, a 400-token cap splits a typical page into 3-4 chunks — enough granularity for precise retrieval without fragmenting content excessively. A smaller cap would multiply the chunk count (more embedding/storage cost, more chunks too short to be meaningful alone); a larger cap would reduce granularity and risk diluting a chunk's embedding with multiple unrelated ideas.
- **Overlap: 240 characters (~15% of cap).** Overlap exists to prevent losing information right at a split boundary — without it, a sentence or fact split across two chunks by a paragraph or hard-character cut could end up incomplete in both. 15% sits within the commonly-cited 10-20% range for RAG chunk overlap; it wasn't empirically tuned against our own retrieval results — that kind of tuning is only really decidable once the Phase 5 retrieval eval exists to measure against — so it's a standard-practice starting point, and a candidate to revisit once real precision/recall numbers exist.

### Alternatives considered

**Pure fixed-size chunking** (split every N characters regardless of structure) was ruled out because it ignores document semantics entirely — it can cut a sentence or list item in half with no regard for meaning, and this corpus already has clear structure (headings) worth respecting instead.

**Heading-splitting with no size cap** was the first version actually built, and it broke immediately on real data: one page's content (dense inline-styled HTML pasted in as one long block) produced a single 32,136-character "chunk" — over 20x the intended size — because that section had no heading to split further on. That's concrete evidence a size-bound fallback isn't optional polish; heading structure alone doesn't bound chunk size, since a single heading's content can be arbitrarily long.

**Library-based chunking** (LlamaIndex's `SentenceWindowNodeParser`/`HierarchicalNodeParser`, `unstructured`'s `chunk_by_title`) was considered and set aside for this project — `chunk_by_title` in particular is conceptually almost identical to what was built here (split on titles, bound by size), so adopting it wouldn't change the strategy, just replace hand-written, tested code with a library call. Adopting LlamaIndex's indexing would also mean replacing this project's own ingestion/storage pipeline with its abstractions, which runs counter to understanding the mechanics directly.

### Known limitations

- **HTML cleanup is regex-based and pattern-specific**, not a full HTML parser — it handles the artifact patterns actually observed in this corpus (residual Confluence-migration tags, one recurring boilerplate sentence), not necessarily every possible malformed-HTML case in content that hasn't been manually reviewed.
- **Heading text can still carry markdown emphasis syntax** — a heading literally titled `**Blog page - Q's Journal**` keeps its `**`. Cosmetic only: it affects the citation trail's readability, not chunk content or retrieval.
- **Small sections aren't merged with neighbors.** A heading with very little content underneath becomes its own small chunk rather than being combined with an adjacent section. `unstructured`'s `chunk_by_title` does this by default; it was considered but not implemented here, since it wasn't clear it would matter enough to prioritize over the remaining project phases.
- **Hard character-splitting has no natural boundary to respect.** When a single paragraph itself exceeds the size cap, it's cut by raw character count, which can land mid-word or mid-sentence — this only affects the rare paragraphs large enough to trigger it.

## Embedding model selection

**Chosen: `BAAI/bge-small-en-v1.5`, run locally via `sentence-transformers`.**

The course's Anthropic-compatible gateway (`API_ENDPOINT_BASE_URL`) was the first option considered, since weeks 1-2 already authenticate against it — but it's a LiteLLM proxy scoped to a specific model allowlist, and a direct request confirmed it only permits `claude-sonnet-5` and `gpt-5-mini` (both text-generation models). It returns `403 team_model_access_denied` for any embedding model, so it's not an option regardless of provider.

That leaves a hosted embedding API (e.g. OpenAI `text-embedding-3-small`) or a local open-source model. We chose local, for two reasons:

1. **No new external dependency on an already-fragile access path.** The gateway itself is only reachable over VPN; adding a second external provider (a new OpenAI account/key) for embeddings would mean the project depends on two separate credentialed services just to answer a question. A local model removes embeddings from that dependency chain entirely — chunking and retrieval work fully offline once the model is cached.
2. **Retrieval-tuned local models are competitive, not just "good enough."** `bge-small-en-v1.5` (BAAI, 2023) is trained specifically for retrieval with asymmetric query/passage embeddings, and scores competitively with — sometimes above — `text-embedding-3-small` on the MTEB retrieval benchmark, despite being a 130MB model that runs on CPU. The corpus here (~9,000 chunks from 673 real pages) is well within what a CPU-hosted small model handles comfortably, so there's no scale pressure pushing toward a larger hosted model.

Trade-offs accepted: `bge-small-en-v1.5` produces 384-dimensional embeddings (vs. 1536 for `text-embedding-3-small`), which caps how much semantic nuance a single vector can encode, and it's English-focused. Both are fine for this KB's scope. The pgvector schema fixes the vector column at 384 dimensions accordingly.

`EMBEDDING_MODEL` in `.env` records the exact model name used, so the choice is reproducible.

