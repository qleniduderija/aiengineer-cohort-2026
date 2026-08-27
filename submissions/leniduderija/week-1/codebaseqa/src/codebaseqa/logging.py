from .pricing import calculate_query_price

BOX_WIDTH = 48


def handle_cost_logging(model, query_usage, totals):
    query_tokens = query_usage.input_tokens + query_usage.output_tokens
    query_price = calculate_query_price(model, query_usage)

    print()
    print("┌─ Usage " + "─" * (BOX_WIDTH - 8))
    print(f"│ This call:  {query_usage.input_tokens:,} in / {query_usage.output_tokens:,} out "
          f"= {query_tokens:,} tokens · ${query_price:.6f}")
    print(f"│ Session:    {totals['usage_total']:,} tokens · ${totals['price_total']:.6f}")
    print("└" + "─" * (BOX_WIDTH - 1))