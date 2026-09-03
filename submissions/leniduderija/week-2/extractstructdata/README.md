# extractstructdata

A command-line tool that extracts structured data (entities, dates, relationships) from a PDF or web page into a typed, validated JSON schema — powered by the Anthropic API (Claude) with forced tool use.

Built for Week 2 of the AI Engineer Cohort 2026, extending [Week 1's codebaseqa CLI](../../week-1/codebaseqa/).

*This README is being filled in as the project is built — see the project's own commits/progress for current status.*

## Resources

- [Anthropic Claude Cookbooks](https://github.com/anthropics/claude-cookbooks) — officially listed course learning material.
  - [`tool_use/extracting_structured_json.ipynb`](https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/extracting_structured_json.ipynb) — reference for the forced `tool_choice` pattern this project uses to get structured JSON out of Claude. Notably, its examples skip schema validation and error handling entirely (no retry, no `is_error` tool results) — this project's validation layer and malformed-response handling fill exactly that gap.
  - [`tool_use/tool_choice.ipynb`](https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/tool_choice.ipynb) — general reference on `tool_choice` modes (`auto`/`any`/`tool`/`none`).
  - [`capabilities/knowledge_graph/guide.ipynb`](https://github.com/anthropics/claude-cookbooks/blob/main/capabilities/knowledge_graph/guide.ipynb) — closest thematic match (entities + subject/predicate/object relationships), a useful reference for schema shape. It uses `client.messages.parse()` with Pydantic ("structured outputs") rather than tool use, so it wasn't used directly — this project's rubric specifically requires the tool-use/function-calling mechanism — but its `Entity`/`Relation` model design and entity-resolution step were useful design references.
