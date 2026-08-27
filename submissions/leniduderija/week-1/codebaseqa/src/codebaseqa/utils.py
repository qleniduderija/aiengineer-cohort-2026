import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Ask natural-language questions about a codebase."
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the repo to analyze (defaults to the current directory).",
    )
    return parser.parse_args()