# CX Task Spec Reference

The CX Task Spec is a platform-agnostic JSON schema for describing customer support automation tasks.

## Schema

See `src/cx_task_harness/models/` for Pydantic model definitions.

### Top-level: TaskSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique task identifier |
| name | string | yes | Human-readable name |
| description | string | yes | What this task does |
| industry | string | no | Industry category |
| locale | "en" \| "ko" | no | Language (default: "en") |
| trigger | Trigger | yes | Activation condition |
| memory | MemoryVariable[] | no | Temporary variables |
| steps | Step[] | yes | Workflow steps |
| automation_potential | AutomationPotential | no | Feasibility score |
| metadata | object | no | Arbitrary metadata |

### Step Types

| Type | Class | Purpose |
|------|-------|---------|
| agent | AgentStep | LLM-driven conversation |
| code | CodeStep | Programmatic logic |
| message | MessageStep | Fixed message delivery |
| action | ActionStep | Internal operations |
| function | FunctionStep | External API call |
| branch | BranchStep | Conditional routing |
| browser | BrowserStep | Web automation |

### Trigger

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| intent | string | yes | Natural language trigger description |
| keywords | string[] | no | Trigger keywords |
| filters | TriggerFilter[] | no | Condition filters |

### AgentInstruction

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | string | yes | Agent role definition |
| conversation_flow | string[] | yes | Ordered steps |
| exit_conditions | string[] | yes | When to end (min 1) |
| exceptions | string[] | no | Edge case handling |

### MemoryVariable

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | yes | Variable name |
| type | string | yes | "string", "number", "boolean", "object", "array" |
| description | string | yes | What it stores |
