# CX Task Architect — Design Document

## One-liner

**An MCP server that analyzes customer support data, designs automation task specs, and converts them to n8n workflows for visualization and testing.**

---

## 1. Problem

Customer support teams handle thousands of repetitive inquiries daily — order cancellations, delivery tracking, reservation changes. AI agents can automate these, but the bottleneck is **designing the automation**:

- Which inquiries should be automated?
- What should the conversation flow look like?
- What APIs need to be called, and when?
- How should the agent branch based on conditions?

This tool automates the design process itself.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude Code CLI                                │
│  (MCP Client)                                   │
│                                                 │
│  "Analyze this support log and design tasks"    │
└────────────────────┬────────────────────────────┘
                     │ STDIO
┌────────────────────▼────────────────────────────┐
│  cx-task-architect (MCP Server)                 │
│  Python + FastMCP                               │
│                                                 │
│  Tools:                                         │
│  ├─ analyze_support_data    (log → patterns)    │
│  ├─ generate_task_spec      (scenario → spec)   │
│  ├─ convert_to_n8n          (spec → n8n JSON)   │
│  ├─ list_templates          (industry templates) │
│  └─ validate_task_spec      (validation)        │
│                                                 │
│  Resources:                                     │
│  ├─ task-spec-schema        (JSON Schema)       │
│  └─ industry-templates      (per-industry)      │
│                                                 │
│  Prompts:                                       │
│  └─ analyze-and-design      (full pipeline)     │
└─────────────────────────────────────────────────┘
```

---

## 3. CX Task Spec

A platform-agnostic JSON schema for describing customer support automation tasks. Designed to be convertible to any agent platform's native format.

### 3.1 Concepts

| Concept | Description |
|---------|-------------|
| **Trigger** | When should this task start? (intent + filters) |
| **Agent Step** | LLM-driven conversational step with structured instructions |
| **Code Step** | Programmatic logic (validation, API calls) |
| **Message Step** | Fixed message delivery |
| **Action Step** | Internal operations (assign team, set tags, etc.) |
| **Function Step** | External API integration |
| **Browser Step** | Web automation |
| **Branch** | Conditional routing between steps |
| **Memory** | Temporary variables scoped to a single task execution |

### 3.2 Schema (Pydantic Models)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional


# ── Memory ──────────────────────────────────────────

class MemoryVariable(BaseModel):
    """Temporary variable during task execution"""
    key: str = Field(description="Variable name (e.g., 'order_id')")
    type: Literal["string", "number", "boolean", "object", "array"]
    description: str


# ── Trigger ─────────────────────────────────────────

class TriggerFilter(BaseModel):
    """Condition filter for trigger activation"""
    field: str = Field(description="Filter target (e.g., 'customer.tier')")
    operator: Literal["eq", "neq", "contains", "gt", "lt", "in"]
    value: str | list[str]

class Trigger(BaseModel):
    """Task activation condition"""
    intent: str = Field(description="Trigger intent in natural language")
    keywords: list[str] = Field(default_factory=list)
    filters: list[TriggerFilter] = Field(default_factory=list)


# ── Steps ───────────────────────────────────────────

class AgentInstruction(BaseModel):
    """
    Structured instruction for an LLM-driven conversational step.
    
    Defines what the agent should do, how the conversation flows,
    when to exit, and what exceptions to handle.
    """
    role: str = Field(description="Role definition")
    conversation_flow: list[str] = Field(
        description="Ordered conversation steps"
    )
    exit_conditions: list[str] = Field(
        description="Conditions that end this step"
    )
    exceptions: list[str] = Field(
        default_factory=list,
        description="Edge cases and exception handling"
    )

class BranchCondition(BaseModel):
    """Routing condition for branching"""
    condition: str
    variable: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    next_step: str = Field(description="Target step ID")

class Step(BaseModel):
    """A single step in a task"""
    id: str
    name: str
    type: Literal[
        "agent", "code", "message", "action",
        "function", "branch", "browser"
    ]
    
    # Type-specific fields
    instructions: Optional[AgentInstruction] = None        # agent
    code: Optional[str] = None                             # code
    message_content: Optional[str] = None                  # message
    action_type: Optional[str] = None                      # action
    action_params: Optional[dict] = None                   # action
    function_url: Optional[str] = None                     # function
    function_method: Optional[Literal[
        "GET", "POST", "PUT", "DELETE"
    ]] = None                                              # function
    function_body: Optional[dict] = None                   # function
    branches: Optional[list[BranchCondition]] = None       # branch
    default_branch: Optional[str] = None                   # branch
    
    # Common fields
    next_step: Optional[str] = None
    on_failure: Optional[str] = None


# ── Task (top-level) ────────────────────────────────

class AutomationPotential(BaseModel):
    """Automation feasibility assessment"""
    score: float = Field(ge=0, le=1)
    reasoning: str
    estimated_resolution_rate: Optional[float] = Field(
        None, ge=0, le=1
    )

class TaskSpec(BaseModel):
    """
    CX Task Spec — a platform-agnostic schema for
    customer support automation tasks.
    """
    id: str
    name: str
    description: str
    industry: Optional[str] = None
    
    trigger: Trigger
    memory: list[MemoryVariable] = Field(default_factory=list)
    steps: list[Step]
    
    automation_potential: Optional[AutomationPotential] = None
    metadata: dict = Field(default_factory=dict)
```

---

## 4. MCP Tools

### 4.1 `analyze_support_data`

Analyzes support conversation logs to identify repeating patterns and recommend automatable tasks.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `str` | CSV or JSON array of support logs |
| `industry` | `str?` | Industry hint for better analysis |
| `min_frequency` | `int` | Minimum occurrence threshold (default: 5) |

Expected data columns: `timestamp`, `customer_message`, `agent_response`, `resolution_type`, `tags` (optional)

**Output:** Total conversations, intent clusters (with frequency, samples, automation score), recommended tasks, estimated overall automation rate.

**Logic:**
1. Cluster messages by intent using LLM
2. Analyze repetition frequency and resolution patterns
3. Score automation potential (simple FAQ → high, emotional care → low)
4. Generate task recommendations

### 4.2 `generate_task_spec`

Generates a CX Task Spec from a scenario description.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario` | `str` | Natural language scenario description |
| `industry` | `str?` | Industry context |
| `template_id` | `str?` | Base template to extend |
| `analysis_context` | `str?` | Output from `analyze_support_data` |

**Output:** `TaskSpec` JSON

**Logic:**
1. Parse scenario into trigger, steps, and branches
2. Reference industry template if available
3. Structure agent instructions (role, flow, exit conditions, exceptions)
4. Derive required memory variables automatically

### 4.3 `convert_to_n8n`

Converts a CX Task Spec into an importable n8n workflow JSON.

**Input:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_spec` | `str` | TaskSpec JSON string |
| `include_mock_data` | `bool` | Include test fixtures (default: true) |

**Output:** n8n workflow JSON

**Mapping:**
```
trigger       → Webhook Node
agent step    → AI Agent Node (LangChain)
code step     → Code Node (JavaScript)
message step  → Respond to Webhook
action step   → HTTP Request / Set Node
function step → HTTP Request Node
branch step   → IF / Switch Node
memory        → Set Node (initialized at workflow start)
```

### 4.4 `list_templates`

Returns pre-built task templates organized by industry.

**Initial templates:**
- `ecommerce/order-cancel` — Order cancellation & refund
- `ecommerce/exchange-return` — Exchange & return processing
- `ecommerce/delivery-tracking` — Delivery status inquiry
- `ecommerce/size-stock-check` — Size & stock availability
- `travel/reservation-change` — Reservation modification
- `travel/reservation-cancel` — Reservation cancellation
- `saas/subscription-manage` — Subscription change & cancellation
- `medical/appointment-change` — Appointment rescheduling

### 4.5 `validate_task_spec`

Validates structural integrity of a task spec.

**Checks:**
- All `next_step` references point to existing step IDs
- All branch targets are valid
- Trigger is defined
- No circular references
- Agent steps have exit conditions

---

## 5. Project Structure

```
cx-task-architect/
├── pyproject.toml
├── README.md
├── LICENSE
│
├── src/
│   └── cx_task_architect/
│       ├── __init__.py
│       ├── server.py              # FastMCP server entrypoint
│       ├── models/
│       │   ├── __init__.py
│       │   ├── task_spec.py       # CX Task Spec Pydantic models
│       │   └── analysis.py        # Analysis result models
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── analyzer.py        # analyze_support_data
│       │   ├── generator.py       # generate_task_spec
│       │   ├── converter.py       # convert_to_n8n
│       │   ├── templates.py       # list_templates
│       │   └── validator.py       # validate_task_spec
│       ├── templates/
│       │   ├── ecommerce/
│       │   │   ├── order_cancel.json
│       │   │   ├── exchange_return.json
│       │   │   └── delivery_tracking.json
│       │   ├── travel/
│       │   │   └── reservation_change.json
│       │   └── saas/
│       │       └── subscription_manage.json
│       └── n8n/
│           ├── __init__.py
│           ├── mapper.py          # TaskSpec → n8n JSON conversion
│           └── node_templates.py  # n8n node JSON templates
│
├── tests/
│   ├── test_models.py
│   ├── test_analyzer.py
│   ├── test_generator.py
│   ├── test_converter.py
│   └── fixtures/
│       └── sample_support_logs.csv
│
└── docs/
    └── TASK_SPEC.md               # Spec reference
```

---

## 6. Installation (Claude Code)

```bash
# Via FastMCP
fastmcp install claude-code src/cx_task_architect/server.py \
  --with anthropic --with pydantic

# Or manually
claude mcp add cx-task-architect \
  -- uv run --with fastmcp --with anthropic --with pydantic \
  fastmcp run src/cx_task_architect/server.py
```

---

## 7. Usage Example

```
User: "Analyze this CSV support log and find automatable tasks"
Claude: [analyze_support_data]
        → "Found 3 patterns in 452 conversations:
           1. Order cancellation (127, score 0.92)
           2. Delivery tracking (98, score 0.88)
           3. Size exchange (67, score 0.75)"

User: "Design the order cancellation task"
Claude: [generate_task_spec]
        → TaskSpec JSON + explanation

User: "Convert it to n8n"
Claude: [convert_to_n8n]
        → n8n workflow JSON
        → "Import this into n8n to visualize and test the flow"
```

---

## 8. Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| MCP Server | FastMCP (Python) | Native Claude Code support, clean decorator API |
| Schema | Pydantic v2 | Type safety + auto JSON Schema generation |
| LLM | Anthropic SDK | Support log analysis and task generation |
| Package mgmt | uv | FastMCP recommended |
| Tests | pytest | Standard |

---

## 9. Implementation Priority

| Order | Item | Rationale |
|-------|------|-----------|
| 1 | `models/task_spec.py` | Core schema — everything depends on this |
| 2 | `server.py` + tool stubs | MCP server skeleton |
| 3 | `templates/` | Demo data for testing |
| 4 | `tools/generator.py` | Scenario → task spec (core value) |
| 5 | `n8n/mapper.py` | Task spec → n8n conversion |
| 6 | `tools/analyzer.py` | Support log analysis (requires LLM) |
| 7 | `tools/validator.py` | Structural validation |
