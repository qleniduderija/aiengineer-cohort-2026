from .ingest import read_pdf, fetch_url
from .tools import call_extraction_tool
from .validate import validate_extraction
from .errors import SchemaValidationError
from .constants import MAX_DOCUMENT_CHARS, MAX_TOKENS


def ingest_document(source):
    if source.startswith("http://") or source.startswith("https://"):
        return fetch_url(source)
    return read_pdf(source)


def extract_document(client, model, source):
    document_text = ingest_document(source)  # raises IngestionError

    if len(document_text) > MAX_DOCUMENT_CHARS:
        document_text = document_text[:MAX_DOCUMENT_CHARS] + f"\n... truncated at {MAX_DOCUMENT_CHARS} characters"

    print("DOCUMENT: ", document_text)
    content = f"Extract structured data from the document below.\n\n<document>\n{document_text}\n</document>"

    messages = [{"role": "user", "content": content}]

    for attempt in range(2):  # 1 initial try + 1 retry
        response = call_extraction_tool(client, model, messages)

        if response.stop_reason == "max_tokens":
            raise SchemaValidationError(
                f"Response was truncated at the {MAX_TOKENS}-token limit before Claude could finish"
            )

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise SchemaValidationError("Claude did not return a tool call")

        try:
            validate_extraction(tool_use_block.input)
            return tool_use_block.input
        except SchemaValidationError as e:
            if attempt == 1:
                raise

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": str(e),
                    "is_error": True,
                }],
            })
