import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic
import anthropic
from .usage import calculate_total_usage
from .pricing import calculate_total_pricing
from .api_error import handle_api_error
from .chat import add_assistant_message, add_user_message
from .tools import TOOLS, run_tools
from .utils import parse_args
from .logging import handle_cost_logging
from .constants import SYSTEM_PROMPT, MAX_TOKENS


def chat(repo_path):
    client = Anthropic(
        base_url=os.environ.get("API_ENDPOINT_BASE_URL")
    )
    model=os.environ.get("CLAUDE_MODEL")

    system_prompt = SYSTEM_PROMPT.format(repo_path=repo_path)

    messages = []
    totals = {
        "usage_total": 0,
        "price_total": 0,
    }

    print(f"codebaseqa — ask questions about the codebase at: {repo_path}")
    print("Type your question and press Enter. Press Ctrl+C to quit.")

    while True:

        print("\n")
        user_input = input("> ")
        print(user_input)
        print("\n")

        add_user_message(messages, user_input)

        try:
            while True:
                with client.messages.stream(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    system=system_prompt,
                    tools=TOOLS
                ) as stream:
                    for text in stream.text_stream:

                        print(text, end="")

                    final_message = stream.get_final_message()

                add_assistant_message(messages, final_message.content)

                current_usage = final_message.usage
                totals = {
                    "usage_total": calculate_total_usage(totals["usage_total"], current_usage),
                    "price_total": calculate_total_pricing(model, totals["price_total"], current_usage),
                }
                handle_cost_logging(model, current_usage, totals)

                if final_message.stop_reason == "max_tokens":
                    print(f"\n\n[Warning: response was cut off — hit the {MAX_TOKENS}-token limit before finishing. Increase MAX_TOKENS in constants.py or ask a narrower question.]")

                if final_message.stop_reason != "tool_use":
                    break

                tool_results = run_tools(final_message, repo_path)
                add_user_message(messages, tool_results)

        except anthropic.APIError as e:
            handle_api_error(e)
        except ValueError as e:
            print(f"\n[{e}]")
        


def main() -> None:
    load_dotenv()

    args = parse_args()
    repo_path = os.path.abspath(args.repo_path)

    if not os.path.isdir(repo_path):
        print(f"[Error: '{repo_path}' is not a directory]")
        sys.exit(1)

    chat(repo_path)

    


