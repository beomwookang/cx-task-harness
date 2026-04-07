# CX Task Harness — Design Spec

> Approved: 2026-04-07
> Status: Ready for implementation planning

---

## 1. Overview

**cx-task-harness** is an open-source MCP server plugin for Claude Code that converts customer support data into automation workflow specs and n8n workflows.

**Core pipeline:**
```
Support data → /analyze → Automation patterns
  → /design → CX Task Spec (JSON)
    → validate_task_spec → convert_to_n8n → validate_n8n
      → /guide → Setup guide (Markdown)
```

**Key design decision:** Hybrid architecture — deterministic logic runs in the MCP server (Python), LLM-driven tasks are handled by Claude Code natively via CLAUDE.md and slash commands.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│  Claude Code CLI                                    │
│  CLAUDE.md (workflow guide)                         │
│  Slash commands (/analyze, /design, /guide)         │
└────────────────────┬────────────────────────────────┘
                     │ STDIO (MCP)
┌────────────────────▼────────────────────────────────┐
│  cx-task-harness (MCP Server)                       │
│  Python + FastMCP                                   │
│                                                     │
│  Tools (deterministic):                             │
│  ├─ validate_task_spec   (TaskSpec validation)      │
│  ├─ convert_to_n8n       (TaskSpec → n8n JSON)      │
│  ├─ validate_n8n         (n8n JSON Schema check)    │
│  └─ list_templates       (industry templates)       │
│                                                     │
│  Resources:                                         │
│  ├─ task-spec-schema     (JSON Schema)              │
│  └─ templates/*          (8 templates × 2 locales)  │
└─────────────────────────────────────────────────────┘
```

### Why Hybrid?

| Concern | MCP Server | Claude Code Native |
|---------|------------|-------------------|
| JSON transformation | Best (deterministic Python) | Overkill |
| Structural validation | Best (Pydantic, graph traversal) | Unreliable |
| Intent clustering | Can't (no LLM) | Best |
| Task spec design | Can't (no LLM) | Best |
| Prompt iteration speed | Slow (server restart) | Instant (edit file) |

---

## 3. CX Task Spec Schema (Discriminated Union)

### 3.1 Common Base

```python
class StepBase(BaseModel):
    id: str
    name: str
    next_step: Optional[str] = None
    on_failure: Optional[str] = None
```

### 3.2 Step Types

```python
class AgentStep(StepBase):
    type: Literal["agent"] = "agent"
    instructions: AgentInstruction          # required

class CodeStep(StepBase):
    type: Literal["code"] = "code"
    code: str
    language: Literal["javascript", "python"] = "javascript"

class MessageStep(StepBase):
    type: Literal["message"] = "message"
    message_content: str

class ActionStep(StepBase):
    type: Literal["action"] = "action"
    action_type: str                        # "assign_team", "set_tag", "close"
    action_params: dict = Field(default_factory=dict)

class FunctionStep(StepBase):
    type: Literal["function"] = "function"
    function_url: str
    function_method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    function_headers: dict = Field(default_factory=dict)
    function_body: Optional[dict] = None

class BranchStep(StepBase):
    type: Literal["branch"] = "branch"
    branches: list[BranchCondition]
    default_branch: Optional[str] = None
    next_step: None = None                  # routing via branches only

class BrowserStep(StepBase):
    type: Literal["browser"] = "browser"
    url: str
    actions: list[dict]
```

### 3.3 Discriminated Union

```python
Step = Annotated[
    AgentStep | CodeStep | MessageStep | ActionStep |
    FunctionStep | BranchStep | BrowserStep,
    Discriminator("type")
]
```

### 3.4 Supporting Models

```python
class AgentInstruction(BaseModel):
    role: str
    conversation_flow: list[str]
    exit_conditions: list[str]
    exceptions: list[str] = Field(default_factory=list)

class BranchCondition(BaseModel):
    condition: str
    variable: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    next_step: str

class MemoryVariable(BaseModel):
    key: str
    type: Literal["string", "number", "boolean", "object", "array"]
    description: str

class TriggerFilter(BaseModel):
    field: str
    operator: Literal["eq", "neq", "contains", "gt", "lt", "in"]
    value: str | list[str]

class Trigger(BaseModel):
    intent: str
    keywords: list[str] = Field(default_factory=list)
    filters: list[TriggerFilter] = Field(default_factory=list)

class AutomationPotential(BaseModel):
    score: float = Field(ge=0, le=1)
    reasoning: str
    estimated_resolution_rate: Optional[float] = Field(None, ge=0, le=1)
```

### 3.5 TaskSpec (Top-level)

```python
class TaskSpec(BaseModel):
    id: str
    name: str
    description: str
    industry: Optional[str] = None
    locale: Literal["ko", "en"] = "en"
    trigger: Trigger
    memory: list[MemoryVariable] = Field(default_factory=list)
    steps: list[Step]
    automation_potential: Optional[AutomationPotential] = None
    metadata: dict = Field(default_factory=dict)
```

---

## 4. MCP Tools

### 4.1 `validate_task_spec`

```
Input:  task_spec: str (TaskSpec JSON)
Output: { valid: bool, errors: list[str], warnings: list[str] }
```

**Errors (block):**
- Pydantic parse failure (Discriminated Union type mismatch)
- `next_step` references non-existent step ID
- `BranchStep.branches[].next_step` references non-existent step ID
- Circular reference detected (A → B → A)
- AgentStep missing `exit_conditions`
- Trigger `intent` is empty
- Duplicate `memory` variable keys

**Warnings (inform):**
- Unreachable steps (no path leads to them)
- FunctionStep/CodeStep without `on_failure`

### 4.2 `convert_to_n8n`

```
Input:  task_spec: str, include_mock_data: bool = true, target_n8n_version: str = "1.x"
Output: { workflow: dict, setup_required: list[SetupItem] }
```

**Step → n8n node mapping:**

| TaskSpec Step | n8n Node | Notes |
|---------------|----------|-------|
| Trigger | Manual Trigger + Set Node | Memory vars initialized |
| AgentStep | AI Agent (LangChain) | instructions → system message |
| CodeStep | Code Node | language field selects JS/Python |
| MessageStep | Set Node → Respond to Webhook | |
| ActionStep | HTTP Request / Set Node | Varies by action_type |
| FunctionStep | HTTP Request Node | url, method, headers, body mapped |
| BranchStep | IF / Switch Node | branches → conditions |
| BrowserStep | HTTP Request (placeholder) | n8n browser automation limited |

**`setup_required` item:**
```json
{
  "node_id": "func_check_order",
  "node_name": "Order Lookup API",
  "type": "credential",
  "description": "API key required for order management system",
  "fields": ["api_key", "base_url"]
}
```

**Layout:** Auto-placement top→down, branches split left/right. Connections auto-generated from `next_step` and `branches`.

**Mock data:** When `include_mock_data=true`, FunctionStep/ActionStep get mock response Code Nodes inserted so the flow is testable without external APIs.

### 4.3 `validate_n8n`

```
Input:  workflow: str (n8n workflow JSON)
Output: { valid: bool, errors: list[str], n8n_version: str }
```

Validates against n8n workflow JSON Schema. Checks node type validity and connection reference integrity.

### 4.4 `list_templates`

```
Input:  industry?: str, locale: str = "en"
Output: { templates: list[TemplateSummary] }
```

```python
class TemplateSummary(BaseModel):
    id: str                # "ecommerce/order-cancel"
    name: str              # "Order Cancellation & Refund"
    description: str
    industry: str
    locale: str
    steps_count: int
    step_types: list[str]  # ["agent", "function", "branch", "action"]
```

Full TaskSpec accessed via MCP resources.

---

## 5. Claude Code Native (Slash Commands)

### 5.1 `/analyze` — Support Data Analysis

```
Role: Support data analyst
Input: CSV/JSON support log file path
Performs:
1. Read data, cluster messages by intent
2. Score each cluster: frequency, sample messages, automation potential (0-1)
3. Generate recommended task list
Output: Total conversations, intent clusters, recommended tasks, estimated automation rate
Reference: list_templates for industry template matching
```

### 5.2 `/design` — TaskSpec Generation

```
Role: CX automation designer
Input: Automation scenario (natural language)
Performs:
1. Read task-spec-schema resource
2. Reference industry template if available
3. Convert scenario to TaskSpec JSON
4. Validate with validate_task_spec
5. Auto-fix and re-validate on failure
Output: Validated TaskSpec JSON
```

### 5.3 `/guide` — Setup Guide Generation

```
Role: n8n workflow setup consultant
Input: convert_to_n8n result (workflow + setup_required)
Performs:
1. Generate per-item setup instructions
2. Describe node locations in the workflow
3. Concrete guides for API key issuance, endpoint configuration
Output: Markdown setup guide
- Sections: "Ready to run" vs "Manual setup required"
- Checklist per setup item
```

### 5.4 CLAUDE.md

Project-level guide injected into Claude Code context:
- MCP tool usage rules (validate after generate, validate after convert)
- TaskSpec authoring guidelines (unique IDs, exit conditions, on_failure)
- Pipeline orchestration sequence

---

## 6. Templates

8 templates × 2 locales (ko, en) = 16 files.

| Industry | Template ID | Description |
|----------|-------------|-------------|
| ecommerce | order-cancel | Order cancellation & refund |
| ecommerce | exchange-return | Exchange & return processing |
| ecommerce | delivery-tracking | Delivery status inquiry |
| ecommerce | size-stock-check | Size & stock availability |
| travel | reservation-change | Reservation modification |
| travel | reservation-cancel | Reservation cancellation |
| saas | subscription-manage | Subscription change & cancellation |
| medical | appointment-change | Appointment rescheduling |

File naming: `{template_id}.{locale}.json` (e.g., `order_cancel.en.json`)

---

## 7. Testing Strategy

| Layer | Test Type | What |
|-------|-----------|------|
| models/ | Unit | Discriminated Union parsing, valid/invalid JSON |
| tools/validator | Unit | Circular refs, reference integrity, warnings |
| tools/converter | Snapshot | Each template → n8n JSON snapshot |
| tools/converter | Schema | Conversion result passes n8n JSON Schema |
| tools/templates | Unit | All templates parse as valid TaskSpec |
| server | Integration | MCP protocol tool call → response |

**Snapshots:** `tests/snapshots/{template_id}.n8n.json`, updated via `pytest --snapshot-update`.

**n8n Schema:** Pinned to target n8n version. May need to be hand-crafted from actual n8n workflow exports if official schema unavailable.

---

## 8. Project Structure

```
cx-task-harness/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
│
├── src/
│   └── cx_task_harness/
│       ├── __init__.py
│       ├── server.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── task_spec.py
│       │   ├── steps.py
│       │   └── n8n.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── validator.py
│       │   ├── converter.py
│       │   ├── n8n_validator.py
│       │   └── templates.py
│       ├── n8n/
│       │   ├── __init__.py
│       │   ├── mapper.py
│       │   ├── layout.py
│       │   └── node_templates.py
│       └── templates/
│           ├── ecommerce/
│           ├── travel/
│           ├── saas/
│           └── medical/
│
├── claude/
│   ├── CLAUDE.md
│   └── commands/
│       ├── analyze.md
│       ├── design.md
│       └── guide.md
│
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_validator.py
│   ├── test_converter.py
│   ├── test_n8n_validator.py
│   ├── test_templates.py
│   ├── test_server.py
│   ├── snapshots/
│   ├── schemas/
│   │   └── n8n_workflow.schema.json
│   └── fixtures/
│       └── sample_support_logs.csv
│
└── docs/
    └── TASK_SPEC.md
```

---

## 9. Tech Stack

| Component | Technology |
|-----------|-----------|
| MCP Server | FastMCP (Python) |
| Schema | Pydantic v2 |
| Package mgmt | uv |
| Tests | pytest + syrupy (snapshots) |
| n8n validation | jsonschema |
| License | MIT |

---

## 10. Implementation Notes

- **n8n version pinning:** Target latest stable n8n 1.x. Both `convert_to_n8n` and `validate_n8n` accept `target_n8n_version` parameter. n8n JSON structure varies by version.
- **Layout algorithm:** `layout.py` must handle nested branches without node overlap. Start simple (tree layout), iterate.
- **Template-first development:** Complete `ecommerce/order_cancel` end-to-end first (template → validate → convert → n8n validate → guide), then replicate for remaining 7 templates.
- **n8n JSON Schema:** Official schema may not be published. Fallback: export workflows from actual n8n instance and derive schema manually.
- **No ALF references:** The CX Task Spec is designed as a platform-agnostic schema. No direct references to ALF or Channel Talk in the open-source codebase.

---

## 11. Future (v2 Scope)

- `cx-task-harness init` CLI for automated Claude Code setup
- Multi-version n8n schema support
- Community template contribution system
- ALF task editor adapter layer (separate package)
