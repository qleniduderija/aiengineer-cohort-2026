import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract structured data (entities, dates, relationships) from PDF or web page sources."
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help="One or more PDF paths or URLs to extract structured data from.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to write each document's extracted JSON to (default: output).",
    )
    return parser.parse_args()