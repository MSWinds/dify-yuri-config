# Dify Storage Architecture Study: Mapping to a Multi-User AI Application

## 1. Executive Summary

Dify's storage model is a **platform-oriented, multi-tenant SaaS schema** built around **Apps** as the central organizing concept. It was designed to power a no-code/low-code AI application builder, not a single bespoke AI product. This creates a fundamental mismatch with our target architecture where **users, sessions, and artifacts** are the primary domain objects.

**Key findings:**

- Dify stores conversations and messages as first-class business entities, but they are **app-scoped**, not user-scoped. There is no concept of a standalone "user session" independent of an app.
- Workflow execution is richly modeled (`WorkflowRun` → `WorkflowNodeExecution`) and provides the best analog for our `llm_runs`, but it is tightly coupled to Dify's visual workflow engine.
- **There is no artifact model.** Dify treats LLM outputs as message answers — ephemeral text within a conversation, not versioned, persistent domain objects.
- Dify recently added a **human-input-in-the-loop** system (`HumanInputForm`, `HumanInputDelivery`, `HumanInputFormRecipient`) which maps well to our future approval requirements.
- Observability is handled via **external tracing providers** (LangFuse, LangSmith, etc.) with no local trace storage — only a config table (`trace_app_configs`) and async queue export.
- Feedback exists as `MessageFeedback` (like/dislike on messages), but there is no mechanism to attach feedback to a specific artifact or workflow output node.

**Bottom line:** Dify's workflow execution tracking and human-in-the-loop models are worth studying. Its conversation/message model is a poor fit for artifact-centric applications. We should build our own domain model and selectively borrow Dify's patterns for workflow execution tracking and LLM cost accounting.

---

## 2. Core Dify Entities

| Dify Entity | Purpose | Likely Table Type | Truth Type | Closest Match In Our System |
|---|---|---|---|---|
| `accounts` | Platform operator/admin users | Business | Business Truth | `users` (admin side) |
| `end_users` | External app consumers (anonymous or identified) | Business | Business Truth | `users` (consumer side) |
| `tenants` | Workspaces / organizations | Business | Business Truth | No direct equivalent (we're single-tenant) |
| `tenant_account_joins` | User ↔ workspace membership with roles | Bridge | Business Truth | User roles/permissions |
| `apps` | Application definitions (chat, workflow, agent, etc.) | Application / Domain | Business Truth | Our application config (static, not per-user) |
| `app_model_configs` | LLM provider/model/prompt configuration per app | Application / Metadata | Business Truth | LLM configuration |
| `conversations` | Chat sessions scoped to an app + user | Domain | Business Truth | **`sessions`** |
| `messages` | Individual turns within a conversation | Domain / Execution | Business Truth + Execution Truth | Partial match to `llm_runs` |
| `message_feedbacks` | Like/dislike ratings on messages | Domain | Business Truth | **`artifact_feedback`** (partial) |
| `message_annotations` | Gold-standard Q&A pairs for training | Domain | Business Truth | No direct equivalent |
| `workflows` | Visual workflow graph definitions (nodes + edges) | Application / Domain | Business Truth | Our pipeline definition (research→ideas→draft) |
| `workflow_runs` | Individual workflow execution instances | Execution | Execution Truth | **`llm_runs`** (workflow-level) |
| `workflow_node_executions` | Per-node execution within a workflow run | Execution | Execution Truth | **`llm_runs`** (step-level) |
| `workflow_app_logs` | Published app execution audit log | Log | Execution Truth | Audit log |
| `workflow_archive_logs` | Denormalized historical run snapshots | Log / Telemetry | Execution Truth | Analytics/archive table |
| `workflow_pauses` | Pause state during workflow execution | Execution / State | Execution Truth | Human-in-the-loop state |
| `workflow_pause_reasons` | Why a workflow was paused | Execution / Metadata | Execution Truth | Approval request metadata |
| `human_input_forms` | Human-in-the-loop approval forms | Domain / Execution | Business Truth | Future approval workflow |
| `human_input_form_deliveries` | Delivery of approval requests to recipients | Execution | Execution Truth | Notification/delivery tracking |
| `human_input_form_recipients` | Who should receive approval requests | Domain | Business Truth | Approver configuration |
| `message_agent_thoughts` | Agent reasoning chain (tool calls, observations) | Execution | Execution Truth | Agent step logs within `llm_runs` |
| `trace_app_configs` | Per-app tracing provider configuration | Metadata | Observability Truth | Tracing config |
| `datasets` | Knowledge base / RAG document collections | Domain | Business Truth | No direct equivalent (unless we add RAG) |
| `documents` / `document_segments` | Chunked documents for retrieval | Domain | Business Truth | No direct equivalent |
| `dataset_retriever_resources` | Which docs were retrieved for a message | Bridge / Execution | Execution Truth | RAG attribution logs |
| `upload_files` | File storage metadata | Infrastructure | Business Truth | File attachments |
| `conversation_variables` | Persistent workflow state per conversation | State | Execution Truth | Session state/context |
| `providers` / `provider_models` | LLM provider credentials and model registry | Infrastructure / Metadata | Business Truth | Provider config |
| `operation_logs` | Admin action audit trail | Log | Observability Truth | Audit log |

---

## 3. Storage Taxonomy

### Business Tables (product truth, user-facing state)
- `accounts`, `end_users`, `tenants`, `tenant_account_joins`
- `apps`, `app_model_configs`, `sites`, `api_tokens`
- `conversations`, `messages`, `message_feedbacks`, `message_annotations`
- `datasets`, `documents`, `document_segments`
- `human_input_forms`, `human_input_form_recipients`

### Execution Tables (what happened during a run)
- `workflow_runs`, `workflow_node_executions`, `workflow_node_execution_offload`
- `message_agent_thoughts`, `message_chains`
- `conversation_variables`, `workflow_draft_variables`
- `workflow_pauses`, `workflow_pause_reasons`
- `human_input_form_deliveries`

### Log / Archive Tables (historical, non-mutable)
- `workflow_app_logs`, `workflow_archive_logs`
- `operation_logs`, `api_requests`
- `dataset_auto_disable_logs`, `rate_limit_logs`

### Metadata / Configuration Tables
- `trace_app_configs`, `app_annotation_settings`
- `providers`, `provider_models`, `provider_credentials`
- `tenant_default_models`, `tenant_preferred_model_providers`
- `tags`, `tag_bindings`, `tool_label_bindings`

### Bridge / Correlation Tables
- `app_dataset_joins` (app ↔ dataset)
- `dataset_retriever_resources` (message ↔ retrieved documents)
- `dataset_metadata_bindings` (document ↔ metadata)
- `workflow_trigger_logs` (trigger ↔ workflow run)

### Observability Tables (none stored locally)
- Dify has **no local trace/span storage tables**. All observability data is exported async to external providers (LangFuse, LangSmith, Arize Phoenix, etc.) via `TraceQueueManager`. The only local record is `trace_app_configs` (configuration, not data).

---

## 4. Mapping to Our Business Model

### `users` → Dify: `accounts` + `end_users`

Dify splits users into two distinct models:
- **`accounts`**: Platform operators (admin console users) with email/password auth, roles, workspace membership
- **`end_users`**: App consumers, identified by `external_user_id` or anonymous with `session_id`

This split exists because Dify is a platform: the people building apps are different from the people using them. In our system, we likely have one unified `users` table. Dify's `end_users` is the closer analog — it has `external_user_id` and `session_id` fields, but it's app-scoped (each app gets its own end_user records).

**Verdict:** Dify's user model is **not reusable** for us. The dual-user pattern adds complexity we don't need.

### `sessions` → Dify: `conversations`

Dify's `Conversation` model is the closest match to our sessions:
- Scoped to app + user
- Contains `name`, `summary`, `inputs` (JSON), `introduction`
- Tracks `dialogue_count`, `status`, soft-delete via `is_deleted`
- Has `conversation_variables` for persistent state across turns

**Key limitations for our use case:**
- Conversations are **app-scoped** — there's no concept of a cross-app session
- No built-in session expiry or timeout logic
- The `summary` field is auto-generated, not a structured session state object
- No explicit "session metadata" beyond `inputs` JSON blob

**Verdict:** Reasonable structural analog, but we need richer session state (current artifact versions, pipeline progress, user preferences). We should build our own with Dify's `conversation_variables` pattern as inspiration for persistent state.

### `artifacts` → Dify: **No equivalent**

This is the biggest gap. Dify treats LLM outputs as `Message.answer` — a text field within a conversation turn. There is no concept of:
- A persistent, addressable output object
- Versioning (v1, v2, v3 of a draft)
- Branching/lineage across artifacts
- Type-differentiated outputs (research report vs. idea list vs. draft post)

Dify's `parent_message_id` field on `Message` provides **implicit branching** for regenerated responses, but this is thread-level branching (which response to show), not artifact versioning.

`WorkflowRun.outputs` (JSON) stores the final workflow output, but it's a flat JSON blob on an execution record — not a first-class domain object.

**Verdict:** We must build `artifacts` from scratch. Dify's design explicitly does not support this concept.

### `artifact_feedback` → Dify: `message_feedbacks`

Dify's `MessageFeedback` stores:
- `rating` (string — typically "like"/"dislike")
- `content` (optional text)
- `from_source` ("user" or "admin")
- Links to `message_id` and `conversation_id`

This is structurally similar but:
- Feedback is on **messages**, not on artifacts or workflow outputs
- There's no concept of structured feedback (rubric scores, quality dimensions)
- No feedback on individual workflow nodes or intermediate outputs

**Verdict:** Useful pattern to adopt, but we need to target `artifact_id` instead of `message_id`, and support richer feedback schemas.

### `llm_runs` → Dify: `workflow_runs` + `workflow_node_executions` + `messages`

This is where Dify's model is richest. The execution tracking is comprehensive:

**`workflow_runs`** captures:
- `inputs`, `outputs`, `status` (running/succeeded/failed/stopped)
- `total_tokens`, `elapsed_time`, `total_steps`
- `graph` (snapshot of workflow definition at execution time)
- `triggered_from` (debugging, app-run, webhook, schedule)

**`workflow_node_executions`** captures per-node:
- `node_id`, `node_type`, `title`
- `inputs`, `outputs`, `process_data`
- `execution_metadata` (JSON with `total_tokens`, `total_price`, tool info)
- `predecessor_node_id` for execution path
- `elapsed_time`, `status`, `error`
- Large payloads offloaded to object storage via `workflow_node_execution_offload`

**`messages`** captures per-conversation-turn:
- `model_provider`, `model_id` (which LLM was called)
- `message_tokens`, `answer_tokens`, `total_price`, `currency`
- `provider_response_latency`
- `workflow_run_id` (links message to workflow execution)

**Verdict:** This is the strongest part of Dify's model for our use case. The three-tier tracking (run → node → message) with token/cost accounting is well-designed. We should adopt this pattern, mapping it to: `pipeline_run` → `pipeline_step_run` → `llm_call`.

---

## 5. What Dify Does Well

### 1. Workflow Execution Tracking
The `WorkflowRun` → `WorkflowNodeExecution` hierarchy is production-grade. The graph snapshot in `WorkflowRun.graph` means you can always reconstruct what workflow version was executing — essential for debugging and auditing. The offload mechanism for large payloads prevents database bloat while maintaining queryable metadata.

### 2. Token & Cost Accounting
Every LLM call records `message_tokens`, `answer_tokens`, `unit_price`, `total_price`, and `currency` at multiple levels (message, node execution, workflow run). This is well-designed for billing, cost analysis, and model comparison.

### 3. Human-in-the-Loop (Recent Addition)
The `HumanInputForm` → `HumanInputDelivery` → `HumanInputFormRecipient` model is well-structured:
- Form has `form_definition`, `rendered_content`, `status` (waiting/submitted/expired)
- Delivery tracks how/when the form was sent to each recipient
- Submission captures `selected_action_id`, `submitted_data`, `submitted_at`, `submission_user_id`
- Links back to `workflow_run_id` and `node_id`

This directly maps to our future approval workflow needs.

### 4. Multi-Tenant Isolation
Every table has `tenant_id` with composite indexes. Even if we're single-tenant now, adopting this pattern costs little and enables future multi-tenancy.

### 5. Async Trace Export Architecture
The `TraceQueueManager` with queue-based batch export to external providers (LangFuse, LangSmith, etc.) is a clean separation of concerns. Execution continues without blocking on trace export. The 10+ provider integrations demonstrate the pattern's extensibility.

---

## 6. Where Dify Does Not Match Our Needs

### 1. No Artifact Model
The most critical gap. Dify has no concept of a persistent, versioned, typed output object. Everything is either a `Message.answer` (text in a conversation) or a `WorkflowRun.outputs` (JSON blob on an execution record). Neither supports:
- Version lineage (report-v1 → report-v2)
- Branching (idea-set-A vs idea-set-B from same research)
- Type safety (research artifact vs draft artifact vs ideas artifact)
- Independent lifecycle from the conversation that created it

### 2. App-Centric, Not User-Centric
Dify's domain model revolves around `App` as the organizing concept. Everything — conversations, messages, workflows, feedback — is scoped to an app. In our model, the user and their session are primary. A user might interact with multiple pipeline stages in a single session, which doesn't map to Dify's "one app, one conversation" pattern.

### 3. No Local Observability Storage
Dify stores **zero trace data locally**. Everything goes to external providers. If we want to query "show me all LLM calls for this artifact's lineage" or "find the slowest step in yesterday's pipeline runs", we'd need to query an external system. For a self-hosted production system, having local queryable traces is valuable.

### 4. Feedback Is Message-Level Only
`MessageFeedback` is a simple like/dislike on a message. We need feedback on:
- Specific artifacts (not messages)
- Specific workflow outputs (not just the final answer)
- Structured dimensions (accuracy, tone, completeness)

### 5. No Artifact-to-LLM-Run Correlation
There's no bridge table connecting a business output to the specific LLM calls that produced it. `Message.workflow_run_id` links a message to a workflow run, but there's no `artifact_id → workflow_node_execution_id` mapping. In Dify, if you want to find which LLM call produced a particular output, you must trace: message → workflow_run → node_executions, and then parse JSON outputs to find the relevant one.

### 6. Conversation Branching Is Implicit
The `parent_message_id` field supports regeneration branching, but there's no explicit version graph. You can't query "show me all versions of this output" — you'd have to walk the message chain and filter. There's no `version` field on messages.

---

## 7. Recommended Architecture for Us

Based on Dify's design, here is an opinionated recommendation:

### Core Domain Tables (Build from scratch)

```sql
users
├── id, email, name, role, preferences (JSON)
├── created_at, updated_at, last_active_at

sessions
├── id, user_id (FK), name, status, metadata (JSON)
├── current_step (enum: research|ideas|draft)
├── created_at, updated_at, expires_at

artifacts
├── id, session_id (FK), user_id (FK)
├── type (enum: research|ideas|draft|post)
├── version (int), parent_artifact_id (FK, nullable)  -- for lineage
├── branch_label (string, nullable)                    -- for branching
├── content (text/JSON), content_hash
├── status (enum: draft|final|approved|rejected)
├── created_at, updated_at

artifact_feedback
├── id, artifact_id (FK), user_id (FK)
├── rating (enum or int), dimensions (JSON)  -- structured feedback
├── comment (text, nullable)
├── created_at
```

### Execution Tables (Adopt from Dify, adapt)

```sql
pipeline_runs                              -- modeled after workflow_runs
├── id, session_id (FK), user_id (FK)
├── pipeline_version (string)
├── pipeline_graph_snapshot (JSON)         -- from Dify: freeze what ran
├── status (enum: running|succeeded|failed|stopped|paused)
├── inputs (JSON), outputs (JSON)
├── total_tokens, total_cost, elapsed_time
├── created_at, finished_at

pipeline_step_runs                         -- modeled after workflow_node_executions
├── id, pipeline_run_id (FK)
├── step_type (enum: research|ideas|draft)
├── step_index (int)
├── predecessor_step_id (FK, nullable)
├── inputs (JSON), outputs (JSON)
├── output_artifact_id (FK, nullable)      -- KEY: links step to artifact
├── status, error, elapsed_time
├── model_provider, model_id
├── prompt_tokens, completion_tokens, total_cost
├── execution_metadata (JSON)
├── created_at, finished_at

llm_calls                                  -- no direct Dify equivalent (they embed in messages)
├── id, pipeline_step_run_id (FK)
├── provider, model
├── system_prompt (text), user_prompt (text)
├── raw_request (JSON), raw_response (JSON)  -- full OpenAI-format request/response
├── prompt_tokens, completion_tokens, total_tokens
├── latency_ms, cost
├── created_at
```

### Correlation Table (Build new — Dify lacks this)

```sql
artifact_lineage
├── id, artifact_id (FK), source_artifact_id (FK, nullable)
├── pipeline_run_id (FK), pipeline_step_run_id (FK)
├── lineage_type (enum: derived|revised|branched)
├── created_at
```

### Approval Tables (Adopt from Dify's human_input_forms)

```sql
approval_requests                          -- modeled after human_input_forms
├── id, pipeline_run_id (FK), step_type
├── artifact_id (FK)                       -- what needs approval
├── form_definition (JSON), status
├── assignee_user_id (FK)
├── submitted_data (JSON), submitted_at
├── created_at, expires_at
```

### Observability Strategy

**Adopt Dify's external export pattern, but add local trace storage:**

```sql
trace_spans                                -- Dify doesn't store locally; we should
├── id, trace_id, parent_span_id (FK, nullable)
├── span_type (enum: pipeline|step|llm_call|tool|retrieval)
├── entity_id (FK to pipeline_run or step or llm_call)
├── name, status, duration_ms
├── attributes (JSON)
├── created_at

-- Also export async to LangFuse/Datadog via queue (adopt Dify's TraceQueueManager pattern)
```

### Key Design Decisions

| Decision | Recommendation | Rationale |
|---|---|---|
| Artifacts as first-class entities | **Yes, build this** | Dify's biggest gap. Outputs must be addressable, versioned, and independent of conversations. |
| Separate `llm_calls` table | **Yes, build this** | Dify embeds LLM data in `messages` and `workflow_node_executions`. A dedicated table enables querying across all LLM usage regardless of context. |
| `output_artifact_id` on step runs | **Yes, build this** | The critical bridge Dify lacks — connecting execution truth to business truth. |
| Local trace storage | **Yes, minimal** | Store spans locally for operational queries. Export to LangFuse for rich analysis. Don't try to replicate LangFuse locally. |
| Token/cost tracking pattern | **Adopt from Dify** | Their per-call + per-step + per-run rollup pattern is well-proven. |
| Human-in-the-loop model | **Adopt from Dify** | Their `HumanInputForm` → delivery → recipient pattern is clean and directly applicable. |
| Graph snapshot on execution | **Adopt from Dify** | `WorkflowRun.graph` freezes the pipeline definition at execution time. Essential for reproducibility. |
| Conversation as session | **Do not adopt** | Dify's conversation model is too chat-centric. Build sessions with explicit state (current step, active artifacts, pipeline progress). |
| App-centric scoping | **Do not adopt** | We don't need the app abstraction layer. Scope everything to user + session. |
| External-only observability | **Partially adopt** | Export to external providers, but also keep a lightweight local `trace_spans` table for operational queries. |

---

## 8. Open Questions / Unknowns

1. **Dify's `execution_metadata` JSON structure**: The `workflow_node_executions.execution_metadata` field stores per-node metadata including token counts, tool info, and datasource info. The exact schema varies by node type and is not formally defined in the ORM — it's parsed at runtime. We should define a stricter schema for our `pipeline_step_runs.execution_metadata`.

2. **Offload threshold**: Dify offloads large node execution payloads to object storage via `workflow_node_execution_offload`, but the threshold for when offloading triggers is set in application config, not visible in the schema. We should determine appropriate thresholds for our `llm_calls.raw_request/raw_response` storage.

3. **Dify's tracing data retention**: Since Dify stores no traces locally, it's unclear how long trace data persists in external providers or whether Dify handles trace rotation. We need to define retention policies for our local `trace_spans` table.

4. **`conversation_variables` durability**: Dify persists workflow variables per conversation in a separate table. It's unclear whether these survive app upgrades or workflow version changes. For our session state, we should explicitly version the state schema.

5. **Message branching vs. artifact versioning**: Dify's `parent_message_id` creates implicit branches for regenerated responses, but there's no explicit query to "list all versions." Our `artifact_lineage` table makes this explicit, but we should validate the query patterns (e.g., "show full lineage tree for artifact X") perform well with recursive queries.

6. **Human input form expiry and resumption**: Dify's `HumanInputForm` has `expiration_time` and links to `WorkflowPause`, but the state serialization mechanism (`state_object_key` in `workflow_pauses`) stores state in object storage. We need to understand whether our pipeline can similarly serialize/deserialize execution state for pause/resume, or if we need a different approach (e.g., saga pattern with compensating actions).

7. **Multi-step pipeline ordering guarantees**: Dify uses `index` and `predecessor_node_id` on `workflow_node_executions` for ordering. In our linear pipeline (research→ideas→draft), ordering is simpler, but if we add parallel branches later, we'll need a similar DAG-aware execution ordering mechanism.

---

## Appendix: Source Files Analyzed

All analysis was based on direct inspection of the following source files in the Dify codebase:

| File | Contents |
|---|---|
| `api/models/model.py` | Account, App, Conversation, Message, MessageFeedback, MessageAnnotation, EndUser, UploadFile, TraceAppConfig, OperationLog |
| `api/models/workflow.py` | Workflow, WorkflowRun, WorkflowNodeExecutionModel, WorkflowAppLog, WorkflowArchiveLog, WorkflowPause, ConversationVariable |
| `api/models/account.py` | Account, Tenant, TenantAccountJoin |
| `api/models/dataset.py` | Dataset, Document, DocumentSegment, Embedding |
| `api/models/provider.py` | Provider, ProviderModel, TenantDefaultModel, ProviderCredential |
| `api/models/tools.py` | ToolOAuthSystemClient, ApiToolProvider, WorkflowToolProvider, MCPToolProvider, ToolModelInvoke |
| `api/models/human_input.py` | HumanInputForm, HumanInputDelivery, HumanInputFormRecipient |
| `api/models/trigger.py` | TriggerSubscription, WorkflowTriggerLog, WorkflowWebhookTrigger, AppTrigger |
| `api/models/enums.py` | All status and type enumerations |
| `api/core/ops/ops_trace_manager.py` | TraceQueueManager, OpsTraceManager |
| `api/core/ops/entities/trace_entity.py` | Trace info data classes |
| `api/core/memory/token_buffer_memory.py` | Conversation memory management |
| `api/core/app/apps/message_based_app_generator.py` | Conversation/message creation flow |
| `api/core/app/workflow/layers/persistence.py` | Workflow execution persistence |
| `api/core/app/workflow/layers/observability.py` | OpenTelemetry integration |
| `api/migrations/versions/` | 165 migration files (schema evolution history) |
