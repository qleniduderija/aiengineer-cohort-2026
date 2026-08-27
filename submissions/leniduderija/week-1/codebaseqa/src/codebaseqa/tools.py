from pathlib import Path

TOOLS = [
    {
        "name": "list_files",
        "description": "List files in the repository, optionally filtered by a glob pattern. Use this to explore the repo's structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files, e.g. '**/*.py'. Defaults to all files.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a specific file in the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, relative to the repo root.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_code",
        "description": "Search the repository's file contents for a text pattern and return matching lines with their file path and line number. Use this to find where something is defined or used across the codebase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for (case-insensitive substring match).",
                },
                "path_pattern": {
                    "type": "string",
                    "description": "Optional glob pattern to limit which files are searched, e.g. '**/*.py'. Defaults to all files.",
                },
            },
            "required": ["query"],
        },
    },
]

EXCLUDED_DIR_NAMES = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}

MAX_LIST_RESULTS = 200
MAX_SEARCH_RESULTS = 100
MAX_FILE_CHARS = 20000


def _is_excluded(relative_path):
    return any(part in EXCLUDED_DIR_NAMES for part in relative_path.parts)


def _resolve_safe_path(repo_path, relative_path):
    repo_root = Path(repo_path).resolve()
    target = (repo_root / relative_path).resolve()

    if not target.is_relative_to(repo_root):
        raise ValueError(f"Path '{relative_path}' escapes the repository root.")

    return target


def list_files(repo_path, pattern="**/*"):
    repo_root = Path(repo_path).resolve()

    results = []
    for match in repo_root.glob(pattern):
        if not match.is_file():
            continue

        relative = match.relative_to(repo_root)
        if _is_excluded(relative):
            continue

        results.append(str(relative))

        if len(results) >= MAX_LIST_RESULTS:
            results.append(f"... truncated at {MAX_LIST_RESULTS} results")
            break

    return "\n".join(results) if results else "No files matched."


def read_file(repo_path, path):
    target = _resolve_safe_path(repo_path, path)

    if not target.is_file():
        raise ValueError(f"'{path}' is not a file in this repository.")

    content = target.read_text(encoding="utf-8", errors="replace")

    if len(content) > MAX_FILE_CHARS:
        content = content[:MAX_FILE_CHARS] + f"\n... truncated at {MAX_FILE_CHARS} characters"

    return content


def search_code(repo_path, query, path_pattern="**/*"):
    repo_root = Path(repo_path).resolve()
    query_lower = query.lower()

    matches = []
    for match in repo_root.glob(path_pattern):
        if not match.is_file():
            continue

        relative = match.relative_to(repo_root)
        if _is_excluded(relative):
            continue

        try:
            lines = match.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if query_lower in line.lower():
                matches.append(f"{relative}:{line_number}: {line.strip()}")

                if len(matches) >= MAX_SEARCH_RESULTS:
                    matches.append(f"... truncated at {MAX_SEARCH_RESULTS} results")
                    return "\n".join(matches)

    return "\n".join(matches) if matches else "No matches found."


TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "search_code": search_code,
}


def execute_tool(name, repo_path, tool_input):
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: '{name}'")

    return TOOL_FUNCTIONS[name](repo_path, **tool_input)


    
def run_tools(message, repo_path):
    tool_requests = [block for block in message.content if block.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        print(f"\n[Using tool: {tool_request.name}({tool_request.input})]")
        try:
            tool_output = execute_tool(tool_request.name, repo_path, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": tool_output,
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks