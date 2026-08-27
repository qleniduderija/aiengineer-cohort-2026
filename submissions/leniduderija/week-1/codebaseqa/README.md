# codebaseqa

A command-line tool that lets you ask natural-language questions about a codebase and get answers grounded in the actual files — powered by the Anthropic API (Claude) with tool use, so the model reads the real repository on disk instead of guessing.

Built for Week 1 of the AI Engineer Cohort 2026.

## What it does

- **Multi-turn conversation** — ask follow-up questions; the model remembers the conversation and previous answers.
- **Streaming output** — responses print token-by-token as they're generated, not all at once at the end.
- **Codebase exploration via tools** — the model has three tools it can call to investigate the repo before answering:
  - `list_files` — list files in the repo, optionally filtered by a glob pattern.
  - `read_file` — read the contents of a specific file.
  - `search_code` — search file contents for a text pattern and get matching file:line results.
- **Token count and cost logging** — after every API call, prints the exact input/output token counts and dollar cost for that call, plus a running total for the session.
- **Graceful error handling** — network errors, rate limits, bad requests, and unknown-model pricing lookups are caught and printed as clear messages instead of crashing the program.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management and running the project
- An Anthropic-compatible API key

## Setup

1. From this directory (`submissions/leniduderija/week-1/codebaseqa/`), install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file in this directory (it's gitignored — never commit it) with:

   ```
   ANTHROPIC_API_KEY=your-api-key-here
   CLAUDE_MODEL=claude-sonnet-5
   ```

   `API_ENDPOINT_BASE_URL` is optional — only set it if you're routing requests through a custom endpoint/proxy instead of Anthropic's default API URL.

## Usage

Run against any local repo by passing its path. If you omit the path, it defaults to the current directory:

```bash
# Analyze a specific repo
uv run codebaseqa /path/to/some/repo

# Analyze the current directory
uv run codebaseqa

# Try it on this very project's own source
cd submissions/leniduderija/week-1/codebaseqa
uv run codebaseqa
```

Once it starts, type a question and press Enter. Keep asking follow-up questions in the same session — conversation history is preserved. Press Ctrl+C to quit.

Example session:

```
codebaseqa — ask questions about the codebase at: /path/to/codebaseqa
Type your question and press Enter. Press Ctrl+C to quit.

> what does pricing.py do?
[Using tool: list_files({'pattern': '**/*.py'})]
[Using tool: read_file({'path': 'src/codebaseqa/pricing.py'})]

`pricing.py` defines a per-model pricing table and calculates the dollar
cost of a query from its token usage. `calculate_query_price(model, usage)`
looks up the model's input/output rate per million tokens and returns the
cost, raising a ValueError if the model isn't in the table...

----- USAGE -----
Input tokens:  1128
Output tokens:  212
Total tokens per query:  1340
------------------

----- PRICING -----
Total price per query:  0.004784
--------------------
Total TOKENS usage in current session:  1340
Total PRICE in current session: 0.004784

> does it handle unknown models gracefully?
...
```

## Project structure

```
src/codebaseqa/
  __init__.py    # entry point (main), the chat REPL and agentic tool-use loop
  constants.py   # system prompt and MAX_TOKENS
  utils.py       # CLI argument parsing (repo path)
  chat.py        # message-list helpers (add_user_message, add_assistant_message)
  tools.py       # tool schemas + implementations (list_files, read_file, search_code) and path-safety
  usage.py       # token usage logging and session totals
  pricing.py     # per-model pricing table and cost calculation
  api.py         # Anthropic API error handling
```

The model only sees what it asks for through tools — the codebase is never dumped into the prompt wholesale. This keeps the approach workable on repos far larger than the context window, and mirrors how the same conversation would proceed with a human developer exploring an unfamiliar codebase.

## Known limitations

- **Local filesystem only.** Point it at a repo already on disk; it doesn't accept GitHub URLs or clone anything. This was a deliberate scope decision — cloning would add git/network dependencies and, for the GitHub API alternative, a second API token and restrictive rate limits, none of which the assignment required.
- **Pricing table is hardcoded** in `pricing.py` and must be updated manually if Anthropic (or another provider behind your endpoint) changes prices — there's no live pricing API to query.
- **`search_code` does substring matching only** (case-insensitive), not full regex.
- **Results are capped** (file listings, search matches, file size) to avoid blowing up the context window on very large repos — very large files are truncated with a note rather than silently cut off.
- **No conversation persistence** — history resets when you quit; each run starts a fresh conversation.
