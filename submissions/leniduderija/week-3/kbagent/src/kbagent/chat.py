import anthropic

from .api_error import handle_api_error
from .constants import MAX_TOKENS, SYSTEM_PROMPT
from .logging import handle_cost_logging
from .pricing import calculate_total_pricing
from .retrieval import retrieve
from .usage import calculate_total_usage
from .utils import format_context


def add_user_message(messages, content):
    messages.append({"role": "user", "content": content})


def add_assistant_message(messages, content):
    messages.append({"role": "assistant", "content": content})


def answer_question(client, model, messages, question, totals):
    results = retrieve(question)
    context = format_context(results)

    add_user_message(messages, f"Context:\n{context}\n\nQuestion: {question}")

    answer = ""
    try:
        with client.messages.stream(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="")
            final_message = stream.get_final_message()

        add_assistant_message(messages, final_message.content)
        answer = "".join(block.text for block in final_message.content if hasattr(block, "text"))

        totals["usage_total"] = calculate_total_usage(totals["usage_total"], final_message.usage)
        totals["price_total"] = calculate_total_pricing(model, totals["price_total"], final_message.usage)
        handle_cost_logging(model, final_message.usage, totals)

    except anthropic.APIError as e:
        handle_api_error(e)

    return answer, results
