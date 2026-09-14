import csv
import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .chat import answer_question

EVAL_DIR = Path(__file__).parent.parent.parent / "eval"


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def main():
    load_dotenv()

    questions = {q["id"]: q for q in load_jsonl(EVAL_DIR / "questions.jsonl")}
    answers = {a["id"]: a for a in load_jsonl(EVAL_DIR / "answers.jsonl")}
    ids = sorted(questions.keys(), key=lambda x: int(x[1:]))

    client = Anthropic(base_url=os.environ.get("API_ENDPOINT_BASE_URL"))
    model = os.environ.get("CLAUDE_MODEL")

    rows = []
    for i, item_id in enumerate(ids, start=1):
        question = questions[item_id]["question"]
        expected_answer = answers[item_id]["expected_answer"]

        # fresh messages/totals per question — each question is answered
        # independently, not as one long conversation
        messages = []
        totals = {"usage_total": 0, "price_total": 0}
        actual_answer, _ = answer_question(client, model, messages, question, totals)

        rows.append(
            {
                "id": item_id,
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": actual_answer,
            }
        )
        print(f"\n[export] {i}/{len(ids)}: {item_id} done")

    with open(EVAL_DIR / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "expected_answer", "actual_answer"])
        writer.writeheader()
        writer.writerows(rows)

    with open(EVAL_DIR / "results.md", "w") as f:
        f.write("| ID | Question | Expected Answer | Agent's Actual Answer |\n")
        f.write("|---|---|---|---|\n")
        for r in rows:
            f.write(
                f"| {r['id']} | {escape_md(r['question'])} | {escape_md(r['expected_answer'])} "
                f"| {escape_md(r['actual_answer'])} |\n"
            )

    print(f"\n[export] wrote {len(rows)} rows to eval/results.csv and eval/results.md")


if __name__ == "__main__":
    main()
