from .models import RetrievalResult


def format_context(results: list[RetrievalResult]) -> str:
    entries = []

    for result in results:
        trail = " > ".join([result.path, *result.heading_trail])
        entries.append(f"[{trail}]\n{result.text}")

    return "\n\n".join(entries)