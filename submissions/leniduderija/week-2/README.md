Task for WEEK 2 is to extend Week 1's CLI into a structured extraction system. Given a PDF or web page, extract structured data (entities, dates, relationships) into a typed JSON schema.

# Core Technical Requirements
 - Tool use / function calling — extraction must go through Claude's tool-use mechanism, not free-text JSON parsing.
 - Handle edge cases gracefully — bad input documents, unreachable URLs, unsupported formats, etc.
 - Validation layer — checks the LLM's output against the schema before it's treated as trustworthy.

# Acceptance Criteria
 - Works on at least 5 sample documents of different formats.
 - Outputs validate against a documented JSON schema.
 - Handles malformed LLM responses without crashing.

# Resources
 - [Anthropic Claude Cookbooks](https://github.com/anthropics/claude-cookbooks) — officially listed course learning material. See `extractstructdata/README.md` for which specific cookbooks informed this project's design.
