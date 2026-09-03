from .validate import SCHEMA
from .constants import MAX_TOKENS, SYSTEM_PROMPT

TOOLS = [
    {
        "name": "extract_structured_data",
        "description": "Extracts structured entities, dates, and relationships from a source document (PDF or web page)",
        "input_schema": SCHEMA,
    },
]


def call_extraction_tool(client, model, messages):
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_choice={"type": "tool", "name": "extract_structured_data"},
        messages=messages,
    )
    return response