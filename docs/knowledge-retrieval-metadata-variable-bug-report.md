# Knowledge Retrieval Metadata Variable Bug Report

## Summary

In our self-hosted Dify deployment, `Knowledge Retrieval` metadata filter conditions worked when the filter value was entered as a manual constant, but failed when the filter value came from a runtime workflow variable such as `User Input`.

Example:

- Works: `department_name is CISAT`
- Failed before fix: `department_name is {{#start.CISAT#}}`

## Symptoms

- Manual constant values in metadata filter conditions returned expected retrieval results.
- Runtime variables in metadata filter conditions returned empty results.
- Using `is not` with a runtime variable often returned results, which suggested the variable template itself was being compared instead of the resolved value.

## Root Cause

The self-hosted implementation passed `metadata_filtering_conditions` from the workflow node to retrieval services without resolving runtime templates first.

As a result, values such as:

```text
{{#start.CISAT#}}
```

were not converted to:

```text
CISAT
```

before metadata filtering was executed.

Enterprise behavior confirmed that the correct implementation resolves metadata filter values at the workflow node layer using `variable_pool.convert_template(...)` before dispatching the retrieval request.

## Fix

Updated the workflow `KnowledgeRetrievalNode` to resolve manual metadata filter condition values before sending the retrieval request downstream.

Implementation details:

- File: `api/core/workflow/nodes/knowledge_retrieval/knowledge_retrieval_node.py`
- Added resolution of string-based metadata filter values via `self.graph_runtime_state.variable_pool.convert_template(...)`
- Preserved constant behavior
- Preserved numeric values after template resolution
- Trimmed control characters from resolved string values

## Test Coverage

Added a unit test to verify that:

- `{{#start.CISAT#}}` is resolved to `CISAT`
- the resolved value is what gets passed into the retrieval request

Test file:

- `api/tests/unit_tests/core/workflow/nodes/knowledge_retrieval/test_knowledge_retrieval_node.py`

## Verification

Targeted backend tests passed:

```bash
DEBUG=false ./.venv/bin/pytest tests/unit_tests/core/workflow/nodes/knowledge_retrieval/test_knowledge_retrieval_node.py
```

Result:

- `14 passed`

Runtime verification after restarting `api`, `worker`, and `worker_beat` confirmed that metadata filter conditions using runtime variables now work in the affected workflow.

## Operational Note

In this deployment, backend services mount local source code:

- `api`
- `worker`
- `worker_beat`

Therefore a service restart was sufficient; rebuilding the Docker image was not required.
