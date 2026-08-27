# Pricing table on 27/08/2026
PRICING = {
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
}

COST_PER_AMOUNT = 1000000 # 1 million tokens

def calculate_query_price(model, queryUsage):
    if model not in PRICING:
      raise ValueError(f"No pricing data for model '{model}'")

    return PRICING[model]["input"] * (queryUsage.input_tokens / COST_PER_AMOUNT) + PRICING[model]["output"] * (queryUsage.output_tokens / COST_PER_AMOUNT)


def calculate_total_pricing(model, sum, queryUsage):
    query_price = calculate_query_price(model, queryUsage)
    sum += query_price
    return sum