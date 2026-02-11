# Tavily Tool Context Explosion Issue

## Problem

When using the Tavily Search tool in Dify **Agent mode**, the LLM receives an excessively large tool output that can exceed the model's context window, causing the LLM to stop responding or produce empty outputs.

### Root Cause

The official Tavily plugin (`langgenius/dify-official-plugins/tools/tavily/tools/tavily_search.py`) emits **two redundant messages** for every search invocation:

1. `yield self.create_json_message(search_results)` — the **entire** Tavily API JSON response
2. `yield self.create_text_message(text=...)` — a formatted Markdown version of the same results

On the Dify core side, `ToolEngine._convert_tool_response_to_str()` (`api/core/tools/tool_engine.py`) concatenates **both** into a single string that gets fed to the LLM as `ToolPromptMessage.content`. The LLM sees double the content, with the raw JSON dump being especially large (it includes `query`, `answer`, `results[]` with `title`, `url`, `content`, `score`, `raw_content`, `favicon`, plus `images`, `response_time`, `auto_parameters`, `usage`, etc.).

With 5 search results (default), this can easily be 6,000-16,000 tokens. If `include_raw_content` is enabled, it can exceed 50,000+ tokens.

### Symptoms

- LLM produces empty responses after tool calls
- Agent shows typing indicator then clears (reported in [langgenius/dify#16970](https://github.com/langgenius/dify/issues/16970))
- Context length exceeded errors with vLLM or smaller models ([langgenius/dify#22859](https://github.com/langgenius/dify/issues/22859))
- Multi-turn conversations degrade quickly because tool output accumulates in conversation history

## Why Not Fix the Plugin Directly

Tavily is a **marketplace plugin** managed by `plugin_daemon`. Each workspace downloads and runs its own copy. The plugin source lives in `langgenius/dify-official-plugins`, not in this repo. Modifying the plugin source would require forking, rebuilding, and redistributing the plugin package — impractical for a self-hosted deployment.

## Solution (Dify Core)

Modify `ToolEngine._convert_tool_response_to_str()` in `api/core/tools/tool_engine.py` so that **when TEXT messages already exist, redundant JSON messages are not appended** to the LLM prompt string.

### The Change

In `api/core/tools/tool_engine.py`, line 261, change:

```python
if json_parts:
    existing_parts = set(parts)
    parts.extend(p for p in json_parts if p not in existing_parts)
```

to:

```python
if json_parts and not parts:
    parts.extend(json_parts)
```

This means: JSON output is only included when there is **no** TEXT output. When a tool emits both TEXT and JSON (as Tavily and Custom API tools do), only the TEXT is sent to the LLM.

### Impact Assessment

All `create_json_message` call sites in this repo were audited:

| Tool Type | File | TEXT + JSON? | Effect of Change |
|-----------|------|-------------|------------------|
| **Plugin tools** (Tavily, etc.) | Plugin code (external) | Yes — Tavily emits both | JSON skipped, TEXT kept. **Fixes the problem.** |
| **Custom API tools** | `api/core/tools/custom_tool/tool.py` | Yes — emits JSON then TEXT for JSON responses | JSON skipped, TEXT kept (TEXT is the raw HTTP response body). **No functional loss.** |
| **Workflow-as-Tool** | `api/core/tools/workflow_as_tool/tool.py` | Yes, but JSON already has `suppress_output=True` | Already suppressed before this change. **Not affected.** |
| **MCP tools** | `api/core/tools/mcp_tool/tool.py` | **No** — emits JSON only (no TEXT) when content is JSON | `parts` is empty, so `not parts` is True, JSON is kept. **Not affected.** |
| **Builtin tools** (time, webscraper, etc.) | `api/core/tools/builtin_tool/providers/` | Varies per tool | Same logic applies safely. |

### Key Safety Properties

1. **MCP tools are safe**: When MCP returns JSON content, it only yields `create_json_message` without TEXT. `parts` stays empty, so JSON is preserved as before.
2. **Tools that only emit JSON are safe**: The condition `not parts` ensures JSON-only tools keep working.
3. **Tools that emit both are deduplicated**: TEXT takes priority, which is the human-readable formatted version.
4. **Workflow mode is unaffected**: This function is only called in the Agent path (`ToolEngine.agent_invoke`). Workflow tool nodes process messages individually via `tool_node.py` and always collect JSON into `outputs["json"]` regardless.

### Scope

- **Only affects Agent mode** (FC agent runner and CoT agent runner)
- **Does not affect Workflow mode** at all
- **Does not affect any plugin or tool code** — purely a Dify core change
