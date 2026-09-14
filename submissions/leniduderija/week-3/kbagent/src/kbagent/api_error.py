import anthropic
import json

def extract_api_error_message(errorMessage):
    try:
        decoder = json.JSONDecoder()
        inner, _ = decoder.raw_decode(errorMessage.body["error"]["message"])
        return inner["error"]["message"]
    except Exception:
        return errorMessage.message

def handle_api_error(e):
    if isinstance(e, anthropic.RateLimitError):
        print("\n[Rate limited — wait a moment and try again]")
    elif isinstance(e, anthropic.APIConnectionError):
        print("\n[Network error — check your connection]")
    elif isinstance(e, anthropic.APIStatusError):
        human_message = extract_api_error_message(e)
        print(f"\n[API error {e.status_code}]")
        print(f"\n[{human_message}]")
    else:
        print(f"\n[Unexpected error: {e}]")