# Workflow Audit Heuristics

This note captures the practical workflow-audit process used to spot Dify apps that were likely edited outside the UI, especially by directly modifying YAML/JSON/DSL with AI assistance.

It is not a proof system. It is an operational checklist for triage.

## Goal

When a workflow crashes the frontend or looks suspicious, the main question is:

- Was this graph created normally in the Dify UI?
- Was it imported from a normal older template/demo/export?
- Or was it likely rewritten externally, for example by AI editing YAML/JSON directly?

## How We Search

We inspect live data in PostgreSQL from Docker rather than relying only on repository fixtures.

Typical tables:

- `apps`
- `accounts`
- `workflows`

Core field:

- `workflows.graph`

The graph JSON is expanded with SQL using:

```sql
jsonb_array_elements((w.graph)::jsonb -> 'nodes')
```

This lets us inspect:

- node ids
- node positions
- node types
- node payload shape

## How We Compare

We compare suspicious workflows against three baselines:

1. Normal UI-created workflows in the live DB.
2. Class/demo/template-derived workflows in the live DB.
3. Canonical node shapes in the frontend code.

Useful frontend references:

- `web/app/components/workflow/types.ts`
- `web/app/components/workflow/nodes/assigner/types.ts`
- `web/app/components/workflow/nodes/variable-assigner/types.ts`

This matters because some suspicious workflows do not just "look odd"; they use node payloads that do not match the frontend schema.

## Strong Flags

These are the most useful signals.

### 1. Future timestamp-like node ids

Many Dify node ids look like millisecond timestamps.

Example:

- `1780000000001` -> `2026-05-28 20:26:40.001 UTC`

If the workflow itself was created much earlier, but the node ids decode to a date far in the future, that is a strong signal of external graph generation.

Why this matters:

- normal UI creation may produce timestamp-like ids
- but those ids should roughly align with the workflow creation period
- a future timestamp block is hard to explain through ordinary UI editing

### 2. Exact consecutive `+1` node-id sequences across the whole graph

Examples:

- `1780000000001`
- `1780000000002`
- `1780000000003`

This is much stronger than "all ids are numeric".

Why this matters:

- numeric ids alone are common
- exact whole-graph `+1` sequences are uncommon
- they suggest a base id was chosen, then all nodes were generated programmatically

For auditing, we only treat this seriously when:

- all node ids are numeric
- the whole workflow has more than 2 nodes
- the sequence covers the entire graph, not just one or two nodes

### 3. All nodes placed on a clean integer grid

Example:

- `(80, 282)`
- `(380, 220)`
- `(680, 220)`

This is only a supporting signal, not enough by itself.

Why this matters:

- imported demos and some manually laid-out graphs can also look neat
- but integer-only positions become more suspicious when combined with exact id blocks

### 4. Mixed id regimes in the same graph

Example pattern:

- early nodes use ordinary timestamp-style ids
- later nodes switch to a very neat artificial block like:
  - `1774670000010`
  - `1774670000011`
  - `1774670000012`

This often suggests:

- part of the graph was built in UI
- then more nodes were added externally

### 5. Non-UI-looking edge ids

Examples:

- `edge-1`
- `edge-4`
- `e7`

When these are mixed with standard Dify-style ids, it suggests graph JSON may have been assembled or rewritten outside the UI.

### 6. Node payload shape incompatible with frontend schema

This is the strongest technical signal.

Example:

- node `type` says `variable-assigner`
- but payload fields do not match either:
  - the current `assigner` schema, or
  - the legacy `variable-aggregator` schema

This is especially important when the workflow also causes frontend crashes.

## Weak Or Ambiguous Flags

These are not enough to conclude AI editing.

### 1. Numeric node ids by themselves

Normal Dify UI workflows often use numeric ids.

### 2. Old timestamp-like ids

A workflow imported from:

- an older template
- a class demo
- a historical export

may keep old ids that no longer match the app creation time.

This is common and not enough by itself.

### 3. Integer coordinates by themselves

Some students import demos, then make small edits.
Some graphs are just neatly arranged.

### 4. Single-node workflows

A single node will always look trivially "consecutive".
Do not count this as meaningful evidence.

## Practical Classification

Use this rough triage model.

### High confidence

Examples:

- future timestamp-like ids
- exact whole-graph `+1` sequences
- all integer coordinates
- malformed node schema

This combination strongly suggests external graph generation or AI-edited YAML/JSON.

### Medium confidence

Examples:

- exact whole-graph `+1` sequence
- all integer coordinates
- but ids are old, not future
- schema is still valid

This suggests programmatic import or external editing, but not necessarily a broken AI-generated graph.

### Low confidence

Examples:

- numeric ids only
- old imported ids
- neat layout only

This should not be used as a standalone accusation.

## Recommended Audit Flow

1. Locate the app owner, app name, current workflow id, and workflow history in `apps` and `workflows`.
2. Expand `workflows.graph -> nodes` and inspect:
   - `id`
   - `position`
   - `data.type`
   - payload shape
3. Check whether all numeric node ids form an exact `+1` sequence.
4. Convert suspicious ids into timestamps and compare with `workflow.created_at`.
5. Check whether all coordinates are integer-only.
6. Inspect edge ids for non-UI naming patterns.
7. Compare suspicious node payloads against frontend schema definitions.
8. Classify the result as high, medium, or low confidence.

## Script

We use this script to audit exact whole-graph consecutive numeric node ids:

- `scripts/audit_consecutive_node_ids.py`

Example:

```bash
uv run --project api python ../scripts/audit_consecutive_node_ids.py --latest-only
```

What it currently flags:

- workflows where all node ids are numeric
- workflows with more than 2 nodes
- workflows where numeric node ids form an exact `+1` sequence across the graph

It also reports:

- owner
- app
- workflow id
- integer-grid status
- whether the id block appears to be a future timestamp block

## Important Caution

These heuristics are for flagging, not for final proof.

Normal alternative explanations still exist:

- imported old templates
- lab/demo imports
- historical exports
- manual external edits

Final conclusions should be based on multiple reinforcing signals, not one artifact alone.
