import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic
import anthropic

from .api_error import handle_api_error
from .utils import parse_args
from .extract import extract_document
from .errors import IngestionError, SchemaValidationError


def output_filename(index, source):
    if source.startswith("http://") or source.startswith("https://"):
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source).strip("_")
    else:
        stem = Path(source).stem
    return f"{index:02d}_{stem[:60]}.json"


def main() -> None:
    load_dotenv()

    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = Anthropic(
        base_url=os.environ.get("API_ENDPOINT_BASE_URL")
    )
    model = os.environ.get("CLAUDE_MODEL")

    succeeded = 0
    failed = 0

    for index, source in enumerate(args.sources, start=1):
        print(f"\n[{index}/{len(args.sources)}] {source}")

        try:
            result = extract_document(client, model, source)

            out_path = output_dir / output_filename(index, source)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            print(f"  -> wrote {out_path}")
            succeeded += 1

        except (IngestionError, SchemaValidationError) as e:
            print(f"  -> skipped: {e}")
            failed += 1
        except anthropic.APIError as e:
            handle_api_error(e)
            failed += 1

    print(f"\n{succeeded} succeeded, {failed} failed, {len(args.sources)} total")

    if succeeded == 0:
        sys.exit(1)
