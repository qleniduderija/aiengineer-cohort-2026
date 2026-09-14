Task for WEEK 3 is to build an internal Q knowledge base agent by ingesting https://kb.q.agency/api/docs (or an anonymised export) into pgvector, then a chat interface that answers questions about Q's internal processes, policies, and technical standards.

# Core Technical Requirements
 - Chunking Strategy – Implement a structured chunking strategy accompanied by a comprehensive written justification.
 - Embedding Model Selection – Provide a clear engineering rationale for the selection of your embedding model.
 - Retrieval Quality Evaluation – Conduct a retrieval quality evaluation on a test set containing at least twenty (≥20) baseline questions with expected ground-truth answers.

# Project Lifecycle Note
This agent will serve as the core project artefact for the remainder of Phase 1. It will be incrementally upgraded in future weeks: Week 4 will introduce an automated evaluation suite, and Week 6 will enhance the architecture with hybrid search capabilities.

# Note on data
kb.q.agency is Q Agency's internal knowledge base (BookStack). The agent ingests it live via the BookStack API using the runner's own token — nothing derived from it (raw content, cache files, the vector DB) is committed to this public fork; it's all gitignored and regenerated locally on each run. The retrieval-eval question set is committed, but expected ground-truth answers are not (submitted separately). See `kbagent/README.md` for details.

# What was built

`kbagent/` — a working RAG agent covering all three core requirements:
- **Chunking strategy**: hierarchical/structure-aware chunking (split by heading, size-bounded paragraph-packing fallback) with a full written justification grounded in measured corpus statistics — see `kbagent/README.md`'s "Chunking strategy" section.
- **Embedding model selection**: `BAAI/bge-small-en-v1.5`, run locally via `sentence-transformers`, with engineering rationale — see "Embedding model selection".
- **Retrieval quality evaluation**: 28 ground-truth Q&A pairs (generated from real KB content, source page known by construction), scored for hit-rate@5 and MRR — **92.86% hit rate, MRR 0.798**. See "Retrieval quality evaluation".

End to end: BookStack ingestion (with incremental re-fetch based on `updated_at`) → chunking → local embedding → pgvector storage → a fixed retrieve→generate chat pipeline → a basic web chat UI (FastAPI + one HTML page), all verified against the real `kb.q.agency` instance.

# How to run

See `kbagent/README.md`'s Setup section — requires VPN access to Q's network (both `kb.q.agency` and the course's Anthropic gateway are VPN-gated) and a personal BookStack API token.

# What's left unfinished

- **Re-indexing is simple, not incremental**: every run truncates and rebuilds the `chunks` table from scratch rather than only re-embedding changed content (a content-hash/ledger-based approach was considered and deliberately deferred — documented in `kbagent/README.md`'s Architecture section).
- **Single-user web UI**: no per-visitor sessions; one shared conversation/cost-total for the whole process.
- **Chunking cleanup is pattern-specific**: the HTML/boilerplate cleanup regex handles artifacts actually observed in this corpus, not necessarily every case — see the chunking strategy's "Known limitations".
- Per the Project Lifecycle Note above, an automated evaluation suite (Week 4) and hybrid search (Week 6) are intentionally out of scope for this submission.
