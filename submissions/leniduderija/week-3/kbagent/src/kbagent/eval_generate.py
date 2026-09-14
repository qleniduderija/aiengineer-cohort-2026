import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .db import get_connection

EVAL_DIR = Path(__file__).parent.parent.parent / "eval"

SAMPLE_SIZE = 30

GENERATE_QA_TOOL = {
    "name": "generate_qa",
    "description": "Generate a natural question and its correct answer, based only on the given passage.",
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "A natural question a real employee might ask, answerable from this passage alone.",
            },
            "answer": {
                "type": "string",
                "description": "A concise, correct answer based only on this passage.",
            },
        },
        "required": ["question", "answer"],
    },
}


def sample_chunks(conn, n):
    return conn.execute(
        """
        SELECT path, text FROM (
            SELECT path, text, ROW_NUMBER() OVER (PARTITION BY page_id ORDER BY random()) AS rn
            FROM chunks
        ) t
        WHERE rn = 1 AND length(text) > 200
        ORDER BY random()
        LIMIT %s
        """,
        (n,),
    ).fetchall()


def generate_qa(client, model, path, text):
    message = client.messages.create(
        model=model,
        max_tokens=512,
        tools=[GENERATE_QA_TOOL],
        tool_choice={"type": "tool", "name": "generate_qa"},
        messages=[{"role": "user", "content": f"Passage (from '{path}'):\n\n{text}"}],
    )
    for block in message.content:
        if block.type == "tool_use":
            return block.input["question"], block.input["answer"]
    return None, None


def main():
    load_dotenv()

    conn = get_connection()
    chunks = sample_chunks(conn, SAMPLE_SIZE)
    print(f"[eval-gen] sampled {len(chunks)} chunks across distinct pages")

    client = Anthropic(base_url=os.environ.get("API_ENDPOINT_BASE_URL"))
    model = os.environ.get("CLAUDE_MODEL")

    questions = []
    answers = []
    for i, (path, text) in enumerate(chunks, start=1):
        question, answer = generate_qa(client, model, path, text)
        if not question or not answer:
            print(f"[eval-gen] {i}/{len(chunks)}: skipped (no usable Q&A generated)")
            continue

        item_id = f"q{len(questions) + 1}"
        questions.append({"id": item_id, "question": question, "expected_source_path": path})
        answers.append({"id": item_id, "expected_answer": answer})
        print(f"[eval-gen] {i}/{len(chunks)}: {question}")

    EVAL_DIR.mkdir(exist_ok=True)

    with open(EVAL_DIR / "questions.jsonl", "w") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")

    with open(EVAL_DIR / "answers.jsonl", "w") as f:
        for a in answers:
            f.write(json.dumps(a) + "\n")

    print(f"[eval-gen] wrote {len(questions)} Q&A pairs to {EVAL_DIR}")


if __name__ == "__main__":
    main()
