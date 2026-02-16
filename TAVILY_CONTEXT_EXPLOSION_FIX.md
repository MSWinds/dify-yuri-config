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
4. **Workflow mode is unaffected**: This function is only called in the Agent path (`ToolEngine.agent_invoke`). Workflow **tool nodes** process messages individually via `tool_node.py` and always collect JSON into `outputs["json"]` regardless.

### Scope

- **Affects Agent mode** (FC agent runner and CoT agent runner) — both standalone agent app and **workflow/chatflow agent node** (see below).
- **Does not affect Workflow tool node or LLM node** — they do not use this function.
- **Does not affect any plugin or tool code** — purely a Dify core change.

## Rollback

To revert this fix, restore the original deduplication logic in `api/core/tools/tool_engine.py` inside `_convert_tool_response_to_str()`.

Replace:

```python
# Only include JSON when no TEXT output exists (TEXT takes priority).
if json_parts and not parts:
    parts.extend(json_parts)
```

Back to the upstream original:

```python
# Add JSON parts, avoiding duplicates from text parts.
if json_parts:
    existing_parts = set(parts)
    parts.extend(p for p in json_parts if p not in existing_parts)
```

This restores the behavior where both TEXT and JSON are sent to the LLM (the upstream default).

---

## Additional Hardening (FC Agent Runner)

Beyond the Tavily-specific fix above, we applied three additional safeguards to prevent context explosion and agent misbehavior in **Function Calling (FC) mode**.

### 1. Tool Output Truncation (6000 chars)

**File**: `api/core/tools/tool_engine.py` — `_convert_tool_response_to_str()`

The final string returned to the LLM is now capped at **6000 characters** (~1500 tokens). If truncated, a notice is appended:

```
[Output truncated: showing first 6000 of 12345 characters]
```

**Why 6000**: Tavily TEXT-only output for 3 results is typically 6000-10000 chars. 6000 preserves 2-3 complete results (ranked by relevance). With 5 tool calls per turn, worst-case accumulation is ~30000 chars (~7500 tokens) which is manageable for modern models (128k+ context).

**Rollback**: Remove the `MAX_TOOL_OUTPUT_CHARS` constant and the truncation `if` block at the end of `_convert_tool_response_to_str()`, reverting `return result` to `return "".join(parts)`.

### 2. Dead-Loop Detection (3 consecutive empty replies)

**File**: `api/core/agent/fc_agent_runner.py` — `run()`

When the LLM produces **no tool calls** and a **trivially short response** (< 50 chars, e.g. "Ok.", "Let's do it.") for **3 consecutive iterations**, the agent breaks out of the loop and returns the accumulated answer. A warning is logged.

This prevents the scenario where a context-overloaded LLM endlessly outputs reasoning fragments ("I will call the tool now." → "Ok." → "Proceed.") without ever generating a valid function call, burning tokens and confusing the user.

**Rollback**: Remove the `_consecutive_empty_replies` / `_MAX_EMPTY_REPLIES` variables and the dead-loop check block after `final_answer += response + "\n"`.

### 3. JSON Parsing Safety in Tool Call Extraction

**File**: `api/core/agent/fc_agent_runner.py` — `extract_tool_calls()` and `extract_blocking_tool_calls()`

Both methods now wrap `json.loads(arguments)` in `try/except (json.JSONDecodeError, TypeError)`. On failure, the raw argument string is passed as `{"__raw_arguments__": "..."}` so the tool invocation can produce a clear error message instead of crashing the entire agent run.

**Rollback**: Remove the `try/except` blocks and restore the bare `args = json.loads(prompt_message.function.arguments)` calls.

---

## Workflow / Chatflow Agent Node (Plugin Backwards Invocation)

When an **agent node** runs inside a workflow or chatflow, the agent loop runs in the **plugin daemon**. When that agent calls a tool (e.g. Tavily), the plugin calls back to the API at `plugin/{tenant_id}/dispatch/tool/invoke`. The API previously used `ToolEngine.generic_invoke` and returned the **raw** message stream (TEXT + JSON), so the plugin had no way to choose — the LLM saw both and context could explode.

### Change: Plugin tool backwards invocation

**File**: `api/core/plugin/backwards_invocation/tool.py` — `PluginToolBackwardsInvocation.invoke_tool()`

- Collect the full tool message stream, then call `ToolEngine._convert_tool_response_to_str(message_list)` to get the same agent-style string (TEXT priority, 6000-char truncation).
- Return one **TEXT** message with that string to the plugin, then pass through any **binary/link** messages (IMAGE_LINK, BLOB, LINK, FILE, etc.) so the plugin can still show images/links.

So workflow/chatflow **agent node** tool calls now get the same deduplicated, truncated output as standalone agent; workflow **tool nodes** and **LLM nodes** are unchanged.

**Rollback**: In `PluginToolBackwardsInvocation.invoke_tool()`, remove the collection + `_convert_tool_response_to_str` + single TEXT yield; restore returning the raw `response` generator from `ToolFileMessageTransformer.transform_tool_invoke_messages(...)`.
