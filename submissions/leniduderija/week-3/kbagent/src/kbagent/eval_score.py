import json
from pathlib import Path

from dotenv import load_dotenv

from .retrieval import retrieve

EVAL_DIR = Path(__file__).parent.parent.parent / "eval"


def load_questions():
    items = []
    with open(EVAL_DIR / "questions.jsonl") as f:
        for line in f:
            items.append(json.loads(line))
    return items


def score_question(item):
    results = retrieve(item["question"])
    for rank, result in enumerate(results, start=1):
        if result.path == item["expected_source_path"]:
            return rank
    return None


def main():
    load_dotenv()

    items = load_questions()
    hits = 0
    reciprocal_ranks = []

    for item in items:
        rank = score_question(item)
        hit = rank is not None
        hits += hit
        reciprocal_ranks.append(1 / rank if hit else 0)
        status = f"hit @ rank {rank}" if hit else "MISS"
        print(f"[{status}] {item['question']}")

    n = len(items)
    hit_rate = hits / n
    mrr = sum(reciprocal_ranks) / n

    print()
    print(f"Questions evaluated: {n}")
    print(f"Hit rate @ top-k: {hit_rate:.2%}")
    print(f"MRR: {mrr:.3f}")


if __name__ == "__main__":
    main()
