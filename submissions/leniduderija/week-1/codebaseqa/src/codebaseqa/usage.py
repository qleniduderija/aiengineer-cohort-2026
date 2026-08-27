def calculate_total_usage(sum, queryUsage):
    currentTokens = queryUsage.input_tokens + queryUsage.output_tokens
    sum += currentTokens
    return sum


