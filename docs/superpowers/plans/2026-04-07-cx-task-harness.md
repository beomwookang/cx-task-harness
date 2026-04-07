# CX Task Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MCP server plugin for Claude Code that validates CX Task Specs and converts them to n8n workflows, with industry templates and Claude Code native slash commands.

**Architecture:** Hybrid — MCP server handles deterministic logic (validation, conversion, templates), Claude Code handles LLM-driven tasks (analysis, design, guide generation) via CLAUDE.md and slash commands. Pydantic v2 Discriminated Union for type-safe TaskSpec schema.

**Tech Stack:** Python 3.11+, FastMCP, Pydantic v2, uv, pytest, syrupy (snapshots), jsonschema

**Spec:** `docs/superpowers/specs/2026-04-07-cx-task-harness-design.md`

---

## File Structure

```
cx-task-harness/
├── pyproject.toml                          # Project config, dependencies
├── README.md                               # Usage guide
├── LICENSE                                 # MIT
│
├── src/cx_task_harness/
│   ├── __init__.py                         # Package version, exports
│   ├── server.py                           # FastMCP server, tool/resource registration
│   ├── models/
│   │   ├── __init__.py                     # Re-exports all models
│   │   ├── common.py                       # AgentInstruction, BranchCondition, MemoryVariable, TriggerFilter, Trigger, AutomationPotential
│   │   ├── steps.py                        # StepBase, 7 step types, Step union
│   │   ├── task_spec.py                    # TaskSpec top-level model
│   │   └── n8n.py                          # SetupItem, TemplateSummary, validation/conversion result models
│   ├── tools/
│   │   ├── __init__.py                     # Re-exports tool functions
│   │   ├── validator.py                    # validate_task_spec implementation
│   │   ├── converter.py                    # convert_to_n8n (orchestrates n8n/ modules)
│   │   ├── n8n_validator.py                # validate_n8n implementation
│   │   └── templates.py                    # list_templates implementation
│   ├── n8n/
│   │   ├── __init__.py                     # Re-exports
│   │   ├── mapper.py                       # Step → n8n node conversion logic
│   │   ├── layout.py                       # Node coordinate auto-placement
│   │   └── node_templates.py               # n8n node JSON template factories
│   └── templates/                          # Industry template JSON files
│       ├── ecommerce/
│       │   ├── order_cancel.en.json
│       │   ├── order_cancel.ko.json
│       │   ├── exchange_return.en.json
│       │   ├── exchange_return.ko.json
│       │   ├── delivery_tracking.en.json
│       │   ├── delivery_tracking.ko.json
│       │   ├── size_stock_check.en.json
│       │   └── size_stock_check.ko.json
│       ├── travel/
│       │   ├── reservation_change.en.json
│       │   ├── reservation_change.ko.json
│       │   ├── reservation_cancel.en.json
│       │   └── reservation_cancel.ko.json
│       ├── saas/
│       │   ├── subscription_manage.en.json
│       │   └── subscription_manage.ko.json
│       └── medical/
│           ├── appointment_change.en.json
│           └── appointment_change.ko.json
│
├── claude/
│   ├── CLAUDE.md                           # Project-level workflow guide
│   └── commands/
│       ├── analyze.md                      # /analyze slash command
│       ├── design.md                       # /design slash command
│       └── guide.md                        # /guide slash command
│
├── tests/
│   ├── conftest.py                         # Shared fixtures
│   ├── test_models.py                      # Pydantic model tests
│   ├── test_validator.py                   # validate_task_spec tests
│   ├── test_converter.py                   # convert_to_n8n tests + snapshots
│   ├── test_n8n_validator.py               # validate_n8n tests
│   ├── test_templates.py                   # Template loading/validation tests
│   ├── test_server.py                      # MCP integration tests
│   ├── snapshots/                          # syrupy snapshot files (auto-generated)
│   ├── schemas/
│   │   └── n8n_workflow.schema.json        # n8n workflow JSON Schema
│   └── fixtures/
│       └── sample_support_logs.csv         # Sample data for docs/demos
│
└── docs/
    └── TASK_SPEC.md                        # TaskSpec reference documentation
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/cx_task_harness/__init__.py`
- Create: `tests/conftest.py`
- Create: `LICENSE`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "cx-task-harness"
version = "0.1.0"
description = "MCP server that validates CX Task Specs and converts them to n8n workflows"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0",
    "pydantic>=2.0.0",
    "jsonschema>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "syrupy>=4.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cx_task_harness"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create package init**

```python
# src/cx_task_harness/__init__.py
"""CX Task Harness — MCP server for CX automation task specs and n8n workflows."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create directory structure**

Run:
```bash
mkdir -p src/cx_task_harness/{models,tools,n8n,templates/{ecommerce,travel,saas,medical}}
mkdir -p tests/{snapshots,schemas,fixtures}
mkdir -p claude/commands
mkdir -p docs
touch src/cx_task_harness/models/__init__.py
touch src/cx_task_harness/tools/__init__.py
touch src/cx_task_harness/n8n/__init__.py
```

- [ ] **Step 4: Create LICENSE**

```
MIT License

Copyright (c) 2026 cx-task-harness contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: Create conftest.py**

```python
# tests/conftest.py
"""Shared test fixtures for cx-task-harness."""

import pytest


@pytest.fixture
def minimal_task_spec_dict() -> dict:
    """Minimal valid TaskSpec as a Python dict."""
    return {
        "id": "test-task",
        "name": "Test Task",
        "description": "A minimal test task",
        "trigger": {
            "intent": "test intent",
        },
        "steps": [
            {
                "id": "step_1",
                "name": "Greet",
                "type": "message",
                "message_content": "Hello!",
            }
        ],
    }


@pytest.fixture
def order_cancel_task_spec_dict() -> dict:
    """Order cancellation TaskSpec with multiple step types."""
    return {
        "id": "ecommerce-order-cancel",
        "name": "Order Cancellation",
        "description": "Handle order cancellation requests",
        "industry": "ecommerce",
        "trigger": {
            "intent": "Customer wants to cancel an order",
            "keywords": ["cancel", "cancellation", "cancel order"],
        },
        "memory": [
            {"key": "order_id", "type": "string", "description": "The order ID to cancel"},
            {"key": "cancel_reason", "type": "string", "description": "Reason for cancellation"},
        ],
        "steps": [
            {
                "id": "greet_and_collect",
                "name": "Greet and Collect Order Info",
                "type": "agent",
                "instructions": {
                    "role": "Friendly customer support agent for order cancellations",
                    "conversation_flow": [
                        "Greet the customer",
                        "Ask for the order ID",
                        "Ask for the reason for cancellation",
                    ],
                    "exit_conditions": [
                        "Order ID and cancellation reason are collected",
                    ],
                    "exceptions": [
                        "If customer does not know order ID, ask for email to look up",
                    ],
                },
                "next_step": "check_order",
            },
            {
                "id": "check_order",
                "name": "Check Order Status",
                "type": "function",
                "function_url": "https://api.example.com/orders/{{order_id}}",
                "function_method": "GET",
                "function_headers": {"Authorization": "Bearer {{api_key}}"},
                "next_step": "branch_cancelable",
                "on_failure": "error_handler",
            },
            {
                "id": "branch_cancelable",
                "name": "Check if Cancelable",
                "type": "branch",
                "branches": [
                    {
                        "condition": "Order is cancelable",
                        "variable": "order_status",
                        "operator": "in",
                        "value": "pending,processing",
                        "next_step": "cancel_order",
                    },
                    {
                        "condition": "Order already shipped",
                        "variable": "order_status",
                        "operator": "eq",
                        "value": "shipped",
                        "next_step": "shipped_message",
                    },
                ],
                "default_branch": "error_handler",
            },
            {
                "id": "cancel_order",
                "name": "Execute Cancellation",
                "type": "function",
                "function_url": "https://api.example.com/orders/{{order_id}}/cancel",
                "function_method": "POST",
                "function_body": {"reason": "{{cancel_reason}}"},
                "next_step": "confirm_message",
                "on_failure": "error_handler",
            },
            {
                "id": "confirm_message",
                "name": "Confirm Cancellation",
                "type": "message",
                "message_content": "Your order {{order_id}} has been successfully cancelled. A refund will be processed within 3-5 business days.",
                "next_step": "close_action",
            },
            {
                "id": "shipped_message",
                "name": "Already Shipped Notice",
                "type": "message",
                "message_content": "Your order {{order_id}} has already been shipped and cannot be cancelled. Would you like to initiate a return instead?",
                "next_step": "assign_to_human",
            },
            {
                "id": "close_action",
                "name": "Close Conversation",
                "type": "action",
                "action_type": "close",
                "action_params": {"tags": ["order-cancelled", "automated"]},
            },
            {
                "id": "assign_to_human",
                "name": "Assign to Human Agent",
                "type": "action",
                "action_type": "assign_team",
                "action_params": {"team": "returns-team"},
            },
            {
                "id": "error_handler",
                "name": "Error Handler",
                "type": "message",
                "message_content": "I'm sorry, I encountered an issue processing your request. Let me connect you with a human agent.",
                "next_step": "assign_to_human",
            },
        ],
    }
```

- [ ] **Step 6: Install dependencies and verify**

Run: `cd /path/to/cx-task-harness && uv sync --dev`
Expected: Dependencies installed successfully

- [ ] **Step 7: Run pytest to verify setup**

Run: `uv run pytest --co`
Expected: Test collection succeeds (0 tests collected, no errors)

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml LICENSE src/ tests/conftest.py claude/ docs/
git commit -m "chore: scaffold cx-task-harness project structure"
```

---

### Task 2: Pydantic Models — Common Types

**Files:**
- Create: `src/cx_task_harness/models/common.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for common models**

```python
# tests/test_models.py
"""Tests for CX Task Spec Pydantic models."""

import pytest
from pydantic import ValidationError


class TestAgentInstruction:
    def test_valid(self):
        from cx_task_harness.models.common import AgentInstruction

        inst = AgentInstruction(
            role="Support agent",
            conversation_flow=["Greet", "Ask order ID"],
            exit_conditions=["Order ID collected"],
        )
        assert inst.role == "Support agent"
        assert len(inst.conversation_flow) == 2
        assert inst.exceptions == []

    def test_exceptions_optional(self):
        from cx_task_harness.models.common import AgentInstruction

        inst = AgentInstruction(
            role="Agent",
            conversation_flow=["Step 1"],
            exit_conditions=["Done"],
            exceptions=["Handle timeout"],
        )
        assert inst.exceptions == ["Handle timeout"]


class TestBranchCondition:
    def test_valid(self):
        from cx_task_harness.models.common import BranchCondition

        bc = BranchCondition(
            condition="Order is cancelable",
            variable="order_status",
            operator="eq",
            value="pending",
            next_step="cancel_order",
        )
        assert bc.next_step == "cancel_order"

    def test_minimal(self):
        from cx_task_harness.models.common import BranchCondition

        bc = BranchCondition(
            condition="Default case",
            next_step="fallback",
        )
        assert bc.variable is None
        assert bc.operator is None


class TestMemoryVariable:
    def test_valid(self):
        from cx_task_harness.models.common import MemoryVariable

        mv = MemoryVariable(key="order_id", type="string", description="The order ID")
        assert mv.key == "order_id"
        assert mv.type == "string"

    def test_invalid_type(self):
        from cx_task_harness.models.common import MemoryVariable

        with pytest.raises(ValidationError):
            MemoryVariable(key="x", type="invalid", description="Bad type")


class TestTriggerFilter:
    def test_valid_string_value(self):
        from cx_task_harness.models.common import TriggerFilter

        tf = TriggerFilter(field="customer.tier", operator="eq", value="vip")
        assert tf.value == "vip"

    def test_valid_list_value(self):
        from cx_task_harness.models.common import TriggerFilter

        tf = TriggerFilter(field="tags", operator="in", value=["urgent", "vip"])
        assert tf.value == ["urgent", "vip"]

    def test_invalid_operator(self):
        from cx_task_harness.models.common import TriggerFilter

        with pytest.raises(ValidationError):
            TriggerFilter(field="x", operator="like", value="y")


class TestTrigger:
    def test_minimal(self):
        from cx_task_harness.models.common import Trigger

        t = Trigger(intent="Cancel order")
        assert t.intent == "Cancel order"
        assert t.keywords == []
        assert t.filters == []

    def test_with_filters(self):
        from cx_task_harness.models.common import Trigger

        t = Trigger(
            intent="Cancel order",
            keywords=["cancel"],
            filters=[{"field": "customer.tier", "operator": "eq", "value": "vip"}],
        )
        assert len(t.filters) == 1


class TestAutomationPotential:
    def test_valid(self):
        from cx_task_harness.models.common import AutomationPotential

        ap = AutomationPotential(score=0.85, reasoning="High repetition")
        assert ap.score == 0.85
        assert ap.estimated_resolution_rate is None

    def test_score_bounds(self):
        from cx_task_harness.models.common import AutomationPotential

        with pytest.raises(ValidationError):
            AutomationPotential(score=1.5, reasoning="Too high")

        with pytest.raises(ValidationError):
            AutomationPotential(score=-0.1, reasoning="Too low")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cx_task_harness.models.common'`

- [ ] **Step 3: Implement common models**

```python
# src/cx_task_harness/models/common.py
"""Common model types used across CX Task Spec."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentInstruction(BaseModel):
    """Structured instruction for an LLM-driven conversational step."""

    role: str = Field(description="Role definition for the agent")
    conversation_flow: list[str] = Field(description="Ordered conversation steps")
    exit_conditions: list[str] = Field(description="Conditions that end this step")
    exceptions: list[str] = Field(
        default_factory=list, description="Edge cases and exception handling"
    )


class BranchCondition(BaseModel):
    """Routing condition for a branch step."""

    condition: str = Field(description="Human-readable condition description")
    variable: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    next_step: str = Field(description="Target step ID")


class MemoryVariable(BaseModel):
    """Temporary variable scoped to a single task execution."""

    key: str = Field(description="Variable name (e.g., 'order_id')")
    type: Literal["string", "number", "boolean", "object", "array"]
    description: str


class TriggerFilter(BaseModel):
    """Condition filter for trigger activation."""

    field: str = Field(description="Filter target (e.g., 'customer.tier')")
    operator: Literal["eq", "neq", "contains", "gt", "lt", "in"]
    value: str | list[str]


class Trigger(BaseModel):
    """Task activation condition."""

    intent: str = Field(description="Trigger intent in natural language")
    keywords: list[str] = Field(default_factory=list)
    filters: list[TriggerFilter] = Field(default_factory=list)


class AutomationPotential(BaseModel):
    """Automation feasibility assessment."""

    score: float = Field(ge=0, le=1)
    reasoning: str
    estimated_resolution_rate: Optional[float] = Field(None, ge=0, le=1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/models/common.py tests/test_models.py
git commit -m "feat: add common Pydantic models (Trigger, AgentInstruction, etc.)"
```

---

### Task 3: Pydantic Models — Step Types (Discriminated Union)

**Files:**
- Create: `src/cx_task_harness/models/steps.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for step types**

Append to `tests/test_models.py`:

```python
import json


class TestStepTypes:
    def test_agent_step(self):
        from cx_task_harness.models.steps import AgentStep

        step = AgentStep(
            id="greet",
            name="Greet Customer",
            instructions={
                "role": "Support agent",
                "conversation_flow": ["Greet"],
                "exit_conditions": ["Done"],
            },
            next_step="next",
        )
        assert step.type == "agent"
        assert step.instructions.role == "Support agent"

    def test_code_step(self):
        from cx_task_harness.models.steps import CodeStep

        step = CodeStep(
            id="validate",
            name="Validate Input",
            code="return items.length > 0;",
        )
        assert step.type == "code"
        assert step.language == "javascript"

    def test_code_step_python(self):
        from cx_task_harness.models.steps import CodeStep

        step = CodeStep(
            id="validate",
            name="Validate",
            code="return len(items) > 0",
            language="python",
        )
        assert step.language == "python"

    def test_message_step(self):
        from cx_task_harness.models.steps import MessageStep

        step = MessageStep(
            id="msg",
            name="Send Message",
            message_content="Hello!",
        )
        assert step.type == "message"

    def test_action_step(self):
        from cx_task_harness.models.steps import ActionStep

        step = ActionStep(
            id="close",
            name="Close",
            action_type="close",
            action_params={"tags": ["done"]},
        )
        assert step.type == "action"
        assert step.action_params == {"tags": ["done"]}

    def test_function_step(self):
        from cx_task_harness.models.steps import FunctionStep

        step = FunctionStep(
            id="api_call",
            name="Call API",
            function_url="https://api.example.com/orders",
            function_method="GET",
        )
        assert step.type == "function"
        assert step.function_headers == {}
        assert step.function_body is None

    def test_branch_step(self):
        from cx_task_harness.models.steps import BranchStep

        step = BranchStep(
            id="check",
            name="Check Status",
            branches=[
                {"condition": "Is active", "next_step": "active_path"},
                {"condition": "Is inactive", "next_step": "inactive_path"},
            ],
            default_branch="fallback",
        )
        assert step.type == "branch"
        assert step.next_step is None
        assert len(step.branches) == 2

    def test_browser_step(self):
        from cx_task_harness.models.steps import BrowserStep

        step = BrowserStep(
            id="automate",
            name="Browser Action",
            url="https://admin.example.com",
            actions=[
                {"action": "click", "selector": "#btn"},
            ],
        )
        assert step.type == "browser"


class TestStepDiscriminatedUnion:
    def test_parse_agent_step(self):
        from pydantic import TypeAdapter
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        data = {
            "id": "s1",
            "name": "Agent",
            "type": "agent",
            "instructions": {
                "role": "Agent",
                "conversation_flow": ["Step 1"],
                "exit_conditions": ["Done"],
            },
        }
        step = adapter.validate_python(data)
        assert step.type == "agent"
        assert step.__class__.__name__ == "AgentStep"

    def test_parse_message_step(self):
        from pydantic import TypeAdapter
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        data = {
            "id": "s1",
            "name": "Msg",
            "type": "message",
            "message_content": "Hi",
        }
        step = adapter.validate_python(data)
        assert step.__class__.__name__ == "MessageStep"

    def test_parse_invalid_type(self):
        from pydantic import TypeAdapter, ValidationError
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        with pytest.raises(ValidationError):
            adapter.validate_python({"id": "s1", "name": "Bad", "type": "nonexistent"})

    def test_parse_from_json_string(self):
        from pydantic import TypeAdapter
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        json_str = json.dumps({
            "id": "s1",
            "name": "Code",
            "type": "code",
            "code": "return 1;",
        })
        step = adapter.validate_json(json_str)
        assert step.type == "code"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py::TestStepTypes -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cx_task_harness.models.steps'`

- [ ] **Step 3: Implement step types**

```python
# src/cx_task_harness/models/steps.py
"""Step type models with Pydantic Discriminated Union."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Discriminator, Field

from cx_task_harness.models.common import AgentInstruction, BranchCondition


class StepBase(BaseModel):
    """Common fields for all step types."""

    id: str
    name: str
    next_step: Optional[str] = None
    on_failure: Optional[str] = None


class AgentStep(StepBase):
    type: Literal["agent"] = "agent"
    instructions: AgentInstruction


class CodeStep(StepBase):
    type: Literal["code"] = "code"
    code: str
    language: Literal["javascript", "python"] = "javascript"


class MessageStep(StepBase):
    type: Literal["message"] = "message"
    message_content: str


class ActionStep(StepBase):
    type: Literal["action"] = "action"
    action_type: str
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
    next_step: None = None


class BrowserStep(StepBase):
    type: Literal["browser"] = "browser"
    url: str
    actions: list[dict]


Step = Annotated[
    AgentStep | CodeStep | MessageStep | ActionStep | FunctionStep | BranchStep | BrowserStep,
    Discriminator("type"),
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/models/steps.py tests/test_models.py
git commit -m "feat: add step type models with Discriminated Union"
```

---

### Task 4: Pydantic Models — TaskSpec & Exports

**Files:**
- Create: `src/cx_task_harness/models/task_spec.py`
- Create: `src/cx_task_harness/models/n8n.py`
- Modify: `src/cx_task_harness/models/__init__.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for TaskSpec**

Append to `tests/test_models.py`:

```python
class TestTaskSpec:
    def test_minimal(self, minimal_task_spec_dict):
        from cx_task_harness.models.task_spec import TaskSpec

        spec = TaskSpec(**minimal_task_spec_dict)
        assert spec.id == "test-task"
        assert spec.locale == "en"
        assert spec.memory == []
        assert spec.automation_potential is None
        assert len(spec.steps) == 1

    def test_full_order_cancel(self, order_cancel_task_spec_dict):
        from cx_task_harness.models.task_spec import TaskSpec

        spec = TaskSpec(**order_cancel_task_spec_dict)
        assert spec.id == "ecommerce-order-cancel"
        assert spec.industry == "ecommerce"
        assert len(spec.memory) == 2
        assert len(spec.steps) == 9
        # Check discriminated union resolved correctly
        assert spec.steps[0].__class__.__name__ == "AgentStep"
        assert spec.steps[1].__class__.__name__ == "FunctionStep"
        assert spec.steps[2].__class__.__name__ == "BranchStep"

    def test_roundtrip_json(self, minimal_task_spec_dict):
        from cx_task_harness.models.task_spec import TaskSpec

        spec = TaskSpec(**minimal_task_spec_dict)
        json_str = spec.model_dump_json()
        spec2 = TaskSpec.model_validate_json(json_str)
        assert spec == spec2

    def test_korean_locale(self, minimal_task_spec_dict):
        from cx_task_harness.models.task_spec import TaskSpec

        minimal_task_spec_dict["locale"] = "ko"
        spec = TaskSpec(**minimal_task_spec_dict)
        assert spec.locale == "ko"

    def test_invalid_locale(self, minimal_task_spec_dict):
        from cx_task_harness.models.task_spec import TaskSpec

        minimal_task_spec_dict["locale"] = "fr"
        with pytest.raises(ValidationError):
            TaskSpec(**minimal_task_spec_dict)


class TestN8nModels:
    def test_setup_item(self):
        from cx_task_harness.models.n8n import SetupItem

        item = SetupItem(
            node_id="func_1",
            node_name="Order API",
            type="credential",
            description="API key needed",
            fields=["api_key", "base_url"],
        )
        assert item.node_id == "func_1"
        assert len(item.fields) == 2

    def test_template_summary(self):
        from cx_task_harness.models.n8n import TemplateSummary

        ts = TemplateSummary(
            id="ecommerce/order-cancel",
            name="Order Cancellation",
            description="Handle order cancellations",
            industry="ecommerce",
            locale="en",
            steps_count=9,
            step_types=["agent", "function", "branch", "action"],
        )
        assert ts.id == "ecommerce/order-cancel"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py::TestTaskSpec -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement TaskSpec**

```python
# src/cx_task_harness/models/task_spec.py
"""Top-level TaskSpec model."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from cx_task_harness.models.common import (
    AutomationPotential,
    MemoryVariable,
    Trigger,
)
from cx_task_harness.models.steps import Step


class TaskSpec(BaseModel):
    """CX Task Spec — platform-agnostic schema for CX automation tasks."""

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

- [ ] **Step 4: Implement n8n models**

```python
# src/cx_task_harness/models/n8n.py
"""Models for n8n conversion and validation results."""

from __future__ import annotations

from pydantic import BaseModel


class SetupItem(BaseModel):
    """An item that requires manual setup in the n8n workflow."""

    node_id: str
    node_name: str
    type: str  # "credential", "endpoint", "config"
    description: str
    fields: list[str]


class TemplateSummary(BaseModel):
    """Summary of an industry template."""

    id: str
    name: str
    description: str
    industry: str
    locale: str
    steps_count: int
    step_types: list[str]
```

- [ ] **Step 5: Update models/__init__.py**

```python
# src/cx_task_harness/models/__init__.py
"""CX Task Spec models."""

from cx_task_harness.models.common import (
    AgentInstruction,
    AutomationPotential,
    BranchCondition,
    MemoryVariable,
    Trigger,
    TriggerFilter,
)
from cx_task_harness.models.n8n import SetupItem, TemplateSummary
from cx_task_harness.models.steps import (
    ActionStep,
    AgentStep,
    BranchStep,
    BrowserStep,
    CodeStep,
    FunctionStep,
    MessageStep,
    Step,
    StepBase,
)
from cx_task_harness.models.task_spec import TaskSpec

__all__ = [
    "AgentInstruction",
    "AutomationPotential",
    "BranchCondition",
    "MemoryVariable",
    "Trigger",
    "TriggerFilter",
    "SetupItem",
    "TemplateSummary",
    "ActionStep",
    "AgentStep",
    "BranchStep",
    "BrowserStep",
    "CodeStep",
    "FunctionStep",
    "MessageStep",
    "Step",
    "StepBase",
    "TaskSpec",
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/cx_task_harness/models/ tests/test_models.py
git commit -m "feat: add TaskSpec, n8n models, and models package exports"
```

---

### Task 5: TaskSpec Validator

**Files:**
- Create: `src/cx_task_harness/tools/validator.py`
- Create: `tests/test_validator.py`

- [ ] **Step 1: Write failing tests for validator**

```python
# tests/test_validator.py
"""Tests for validate_task_spec tool."""

import json
import pytest


class TestValidateTaskSpec:
    def test_valid_minimal(self, minimal_task_spec_dict):
        from cx_task_harness.tools.validator import validate_task_spec

        result = validate_task_spec(json.dumps(minimal_task_spec_dict))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_full(self, order_cancel_task_spec_dict):
        from cx_task_harness.tools.validator import validate_task_spec

        result = validate_task_spec(json.dumps(order_cancel_task_spec_dict))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_json(self):
        from cx_task_harness.tools.validator import validate_task_spec

        result = validate_task_spec("not json")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_missing_required_field(self):
        from cx_task_harness.tools.validator import validate_task_spec

        result = validate_task_spec(json.dumps({"id": "x"}))
        assert result["valid"] is False

    def test_invalid_next_step_reference(self, minimal_task_spec_dict):
        from cx_task_harness.tools.validator import validate_task_spec

        minimal_task_spec_dict["steps"][0]["next_step"] = "nonexistent"
        result = validate_task_spec(json.dumps(minimal_task_spec_dict))
        assert result["valid"] is False
        assert any("nonexistent" in e for e in result["errors"])

    def test_invalid_branch_target(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {
                    "id": "b1",
                    "name": "Branch",
                    "type": "branch",
                    "branches": [
                        {"condition": "yes", "next_step": "ghost"},
                    ],
                }
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("ghost" in e for e in result["errors"])

    def test_circular_reference(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {"id": "a", "name": "A", "type": "message", "message_content": "Hi", "next_step": "b"},
                {"id": "b", "name": "B", "type": "message", "message_content": "Hi", "next_step": "a"},
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("circular" in e.lower() for e in result["errors"])

    def test_empty_trigger_intent(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": ""},
            "steps": [{"id": "s", "name": "S", "type": "message", "message_content": "Hi"}],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("intent" in e.lower() for e in result["errors"])

    def test_duplicate_memory_keys(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "memory": [
                {"key": "dup", "type": "string", "description": "A"},
                {"key": "dup", "type": "number", "description": "B"},
            ],
            "steps": [{"id": "s", "name": "S", "type": "message", "message_content": "Hi"}],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("duplicate" in e.lower() for e in result["errors"])

    def test_agent_step_without_exit_conditions(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {
                    "id": "a",
                    "name": "Agent",
                    "type": "agent",
                    "instructions": {
                        "role": "Agent",
                        "conversation_flow": ["Step"],
                        "exit_conditions": [],
                    },
                }
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("exit_conditions" in e for e in result["errors"])


class TestValidatorWarnings:
    def test_unreachable_step(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {"id": "reachable", "name": "R", "type": "message", "message_content": "Hi"},
                {"id": "orphan", "name": "O", "type": "message", "message_content": "Alone"},
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is True  # warnings don't block
        assert any("orphan" in w.lower() for w in result["warnings"])

    def test_function_without_on_failure(self):
        from cx_task_harness.tools.validator import validate_task_spec

        spec = {
            "id": "t",
            "name": "T",
            "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {
                    "id": "f",
                    "name": "API",
                    "type": "function",
                    "function_url": "https://example.com",
                }
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is True
        assert any("on_failure" in w for w in result["warnings"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement validator**

```python
# src/cx_task_harness/tools/validator.py
"""validate_task_spec tool implementation."""

from __future__ import annotations

import json as json_module

from pydantic import ValidationError

from cx_task_harness.models.steps import AgentStep, BranchStep, CodeStep, FunctionStep
from cx_task_harness.models.task_spec import TaskSpec


def validate_task_spec(task_spec: str) -> dict:
    """Validate a CX Task Spec JSON string.

    Returns {"valid": bool, "errors": list[str], "warnings": list[str]}.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Parse JSON + Pydantic validation
    try:
        data = json_module.loads(task_spec)
    except json_module.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": []}

    try:
        spec = TaskSpec(**data)
    except ValidationError as e:
        return {
            "valid": False,
            "errors": [f"Schema validation error: {err['msg']}" for err in e.errors()],
            "warnings": [],
        }

    step_ids = {step.id for step in spec.steps}

    # 2. Empty trigger intent
    if not spec.trigger.intent.strip():
        errors.append("Trigger intent must not be empty")

    # 3. Duplicate memory keys
    mem_keys = [m.key for m in spec.memory]
    seen_keys: set[str] = set()
    for key in mem_keys:
        if key in seen_keys:
            errors.append(f"Duplicate memory variable key: '{key}'")
        seen_keys.add(key)

    # 4. Validate step references
    for step in spec.steps:
        # next_step reference
        if step.next_step is not None and step.next_step not in step_ids:
            errors.append(
                f"Step '{step.id}' references non-existent next_step '{step.next_step}'"
            )

        # on_failure reference
        if step.on_failure is not None and step.on_failure not in step_ids:
            errors.append(
                f"Step '{step.id}' references non-existent on_failure '{step.on_failure}'"
            )

        # Branch targets
        if isinstance(step, BranchStep):
            for branch in step.branches:
                if branch.next_step not in step_ids:
                    errors.append(
                        f"Branch step '{step.id}' references non-existent target '{branch.next_step}'"
                    )
            if step.default_branch is not None and step.default_branch not in step_ids:
                errors.append(
                    f"Branch step '{step.id}' references non-existent default_branch '{step.default_branch}'"
                )

        # Agent exit conditions
        if isinstance(step, AgentStep):
            if not step.instructions.exit_conditions:
                errors.append(
                    f"Agent step '{step.id}' must have at least one exit_conditions entry"
                )

    # 5. Circular reference detection
    if not errors:  # Only check if no reference errors
        _check_circular(spec, errors)

    # 6. Warnings: unreachable steps
    reachable = _find_reachable_steps(spec)
    for step in spec.steps:
        if step.id not in reachable and step != spec.steps[0]:
            warnings.append(f"Step '{step.id}' is unreachable (no path leads to it)")

    # 7. Warnings: FunctionStep/CodeStep without on_failure
    for step in spec.steps:
        if isinstance(step, (FunctionStep, CodeStep)) and step.on_failure is None:
            warnings.append(f"Step '{step.id}' ({step.type}) has no on_failure handler")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _check_circular(spec: TaskSpec, errors: list[str]) -> None:
    """Detect circular references in step graph via DFS."""
    adjacency: dict[str, list[str]] = {}
    for step in spec.steps:
        targets: list[str] = []
        if step.next_step is not None:
            targets.append(step.next_step)
        if step.on_failure is not None:
            targets.append(step.on_failure)
        if isinstance(step, BranchStep):
            for branch in step.branches:
                targets.append(branch.next_step)
            if step.default_branch is not None:
                targets.append(step.default_branch)
        adjacency[step.id] = targets

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {sid: WHITE for sid in adjacency}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in adjacency.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                errors.append(f"Circular reference detected involving step '{neighbor}'")
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    for node in adjacency:
        if color[node] == WHITE:
            dfs(node)


def _find_reachable_steps(spec: TaskSpec) -> set[str]:
    """Find all steps reachable from the first step via BFS."""
    if not spec.steps:
        return set()

    reachable: set[str] = set()
    queue = [spec.steps[0].id]
    step_map = {step.id: step for step in spec.steps}

    while queue:
        current_id = queue.pop(0)
        if current_id in reachable or current_id not in step_map:
            continue
        reachable.add(current_id)
        step = step_map[current_id]

        if step.next_step is not None:
            queue.append(step.next_step)
        if step.on_failure is not None:
            queue.append(step.on_failure)
        if isinstance(step, BranchStep):
            for branch in step.branches:
                queue.append(branch.next_step)
            if step.default_branch is not None:
                queue.append(step.default_branch)

    return reachable
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_validator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/tools/validator.py tests/test_validator.py
git commit -m "feat: add validate_task_spec with reference, circular, and reachability checks"
```

---

### Task 6: n8n Node Templates

**Files:**
- Create: `src/cx_task_harness/n8n/node_templates.py`
- Create: `tests/test_n8n_nodes.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_n8n_nodes.py
"""Tests for n8n node template factories."""


class TestNodeTemplates:
    def test_manual_trigger(self):
        from cx_task_harness.n8n.node_templates import make_manual_trigger

        node = make_manual_trigger()
        assert node["type"] == "n8n-nodes-base.manualTrigger"
        assert "position" in node
        assert "id" in node

    def test_set_node(self):
        from cx_task_harness.n8n.node_templates import make_set_node

        node = make_set_node(
            node_id="set_1",
            name="Init Memory",
            assignments={"order_id": "", "cancel_reason": ""},
        )
        assert node["type"] == "n8n-nodes-base.set"
        assert node["name"] == "Init Memory"

    def test_code_node(self):
        from cx_task_harness.n8n.node_templates import make_code_node

        node = make_code_node(
            node_id="code_1",
            name="Validate",
            code="return items;",
            language="javascript",
        )
        assert node["type"] == "n8n-nodes-base.code"
        assert node["parameters"]["jsCode"] == "return items;"

    def test_code_node_python(self):
        from cx_task_harness.n8n.node_templates import make_code_node

        node = make_code_node(
            node_id="code_1",
            name="Process",
            code="return items",
            language="python",
        )
        assert node["parameters"]["language"] == "python"
        assert node["parameters"]["pythonCode"] == "return items"

    def test_http_request_node(self):
        from cx_task_harness.n8n.node_templates import make_http_request_node

        node = make_http_request_node(
            node_id="http_1",
            name="Call API",
            url="https://api.example.com",
            method="GET",
            headers={"Authorization": "Bearer key"},
        )
        assert node["type"] == "n8n-nodes-base.httpRequest"
        assert node["parameters"]["url"] == "https://api.example.com"
        assert node["parameters"]["method"] == "GET"

    def test_if_node(self):
        from cx_task_harness.n8n.node_templates import make_if_node

        node = make_if_node(
            node_id="if_1",
            name="Check Status",
            conditions=[
                {"variable": "status", "operator": "eq", "value": "active"},
            ],
        )
        assert node["type"] == "n8n-nodes-base.if"

    def test_ai_agent_node(self):
        from cx_task_harness.n8n.node_templates import make_ai_agent_node

        node = make_ai_agent_node(
            node_id="agent_1",
            name="Support Agent",
            system_message="You are a helpful support agent.",
        )
        assert node["type"] == "@n8n/n8n-nodes-langchain.agent"

    def test_all_nodes_have_required_fields(self):
        from cx_task_harness.n8n.node_templates import (
            make_manual_trigger,
            make_set_node,
            make_code_node,
        )

        for node in [
            make_manual_trigger(),
            make_set_node("s1", "S", {}),
            make_code_node("c1", "C", "x", "javascript"),
        ]:
            assert "id" in node
            assert "type" in node
            assert "name" in node
            assert "position" in node
            assert "parameters" in node
            assert "typeVersion" in node
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_n8n_nodes.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement node templates**

```python
# src/cx_task_harness/n8n/node_templates.py
"""Factory functions that produce n8n node JSON dicts."""

from __future__ import annotations

# Default position; layout.py will overwrite these
_DEFAULT_POS = [250, 300]


def _base_node(node_id: str, name: str, node_type: str, type_version: int = 1) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": list(_DEFAULT_POS),
        "parameters": {},
    }


def make_manual_trigger(node_id: str = "trigger") -> dict:
    return _base_node(node_id, "Manual Trigger", "n8n-nodes-base.manualTrigger")


def make_set_node(node_id: str, name: str, assignments: dict) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.set", type_version=3)
    node["parameters"] = {
        "mode": "manual",
        "duplicateItem": False,
        "assignments": {
            "assignments": [
                {"id": f"{node_id}_{k}", "name": k, "value": v, "type": "string"}
                for k, v in assignments.items()
            ]
        },
    }
    return node


def make_code_node(node_id: str, name: str, code: str, language: str) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.code", type_version=2)
    if language == "python":
        node["parameters"] = {"language": "python", "pythonCode": code}
    else:
        node["parameters"] = {"jsCode": code}
    return node


def make_http_request_node(
    node_id: str,
    name: str,
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: dict | None = None,
) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.httpRequest", type_version=4)
    node["parameters"] = {
        "url": url,
        "method": method,
        "options": {},
    }
    if headers:
        node["parameters"]["options"]["headers"] = {
            "parameters": [{"name": k, "value": v} for k, v in headers.items()]
        }
    if body:
        node["parameters"]["sendBody"] = True
        node["parameters"]["bodyParameters"] = {
            "parameters": [{"name": k, "value": str(v)} for k, v in body.items()]
        }
    return node


def make_if_node(node_id: str, name: str, conditions: list[dict]) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.if", type_version=2)
    n8n_conditions = []
    for cond in conditions:
        n8n_conditions.append({
            "id": f"{node_id}_{cond.get('variable', 'cond')}",
            "leftValue": f"={{{{ $json.{cond.get('variable', 'value')} }}}}",
            "rightValue": cond.get("value", ""),
            "operator": {
                "type": "string",
                "operation": _map_operator(cond.get("operator", "eq")),
            },
        })
    node["parameters"] = {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": ""},
            "conditions": n8n_conditions,
            "combinator": "and",
        },
    }
    return node


def make_ai_agent_node(node_id: str, name: str, system_message: str) -> dict:
    node = _base_node(node_id, name, "@n8n/n8n-nodes-langchain.agent", type_version=1)
    node["parameters"] = {
        "text": "={{ $json.chatInput }}",
        "options": {"systemMessage": system_message},
    }
    return node


def make_mock_response_node(node_id: str, name: str, mock_data: dict) -> dict:
    """Creates a Code node that returns mock data instead of calling an API."""
    import json

    code = f"return [{json.dumps({'json': mock_data})}];"
    return make_code_node(node_id, f"[Mock] {name}", code, "javascript")


def _map_operator(op: str) -> str:
    """Map TaskSpec operators to n8n IF node operators."""
    mapping = {
        "eq": "equals",
        "neq": "notEquals",
        "contains": "contains",
        "gt": "gt",
        "lt": "lt",
        "in": "contains",
    }
    return mapping.get(op, "equals")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_n8n_nodes.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/n8n/node_templates.py tests/test_n8n_nodes.py
git commit -m "feat: add n8n node template factory functions"
```

---

### Task 7: n8n Layout Algorithm

**Files:**
- Create: `src/cx_task_harness/n8n/layout.py`
- Create: `tests/test_layout.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_layout.py
"""Tests for n8n node layout algorithm."""


class TestLayout:
    def test_linear_layout(self):
        from cx_task_harness.n8n.layout import compute_layout

        # Simple linear chain: A → B → C
        nodes = [
            {"id": "a", "position": [0, 0]},
            {"id": "b", "position": [0, 0]},
            {"id": "c", "position": [0, 0]},
        ]
        connections = {"a": ["b"], "b": ["c"]}
        compute_layout(nodes, connections, start_id="a")

        # Nodes should be laid out top to bottom
        node_map = {n["id"]: n for n in nodes}
        assert node_map["a"]["position"][1] < node_map["b"]["position"][1]
        assert node_map["b"]["position"][1] < node_map["c"]["position"][1]
        # All on same x
        assert node_map["a"]["position"][0] == node_map["b"]["position"][0]

    def test_branch_layout(self):
        from cx_task_harness.n8n.layout import compute_layout

        # Branch: A → [B, C]
        nodes = [
            {"id": "a", "position": [0, 0]},
            {"id": "b", "position": [0, 0]},
            {"id": "c", "position": [0, 0]},
        ]
        connections = {"a": ["b", "c"]}
        compute_layout(nodes, connections, start_id="a")

        node_map = {n["id"]: n for n in nodes}
        # B and C should be at same y level, different x
        assert node_map["b"]["position"][1] == node_map["c"]["position"][1]
        assert node_map["b"]["position"][0] != node_map["c"]["position"][0]

    def test_no_overlap(self):
        from cx_task_harness.n8n.layout import compute_layout

        nodes = [{"id": f"n{i}", "position": [0, 0]} for i in range(5)]
        connections = {"n0": ["n1", "n2"], "n1": ["n3"], "n2": ["n4"]}
        compute_layout(nodes, connections, start_id="n0")

        positions = [tuple(n["position"]) for n in nodes]
        assert len(set(positions)) == len(positions), "Nodes overlap!"

    def test_empty_graph(self):
        from cx_task_harness.n8n.layout import compute_layout

        nodes: list[dict] = []
        connections: dict[str, list[str]] = {}
        compute_layout(nodes, connections, start_id="")
        # Should not crash
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_layout.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement layout**

```python
# src/cx_task_harness/n8n/layout.py
"""Auto-placement algorithm for n8n workflow nodes.

Uses a tree-based layout: BFS from start node, placing children
at increasing Y levels. Branches split horizontally.
"""

from __future__ import annotations

# n8n canvas constants
X_SPACING = 300  # horizontal gap between branch siblings
Y_SPACING = 200  # vertical gap between levels
START_X = 250
START_Y = 300


def compute_layout(
    nodes: list[dict],
    connections: dict[str, list[str]],
    start_id: str,
) -> None:
    """Mutate node['position'] in-place with auto-computed coordinates.

    Args:
        nodes: List of n8n node dicts (must have 'id' and 'position').
        connections: Adjacency map {source_id: [target_ids]}.
        start_id: The ID of the entry node.
    """
    if not nodes:
        return

    node_map = {n["id"]: n for n in nodes}
    placed: set[str] = set()

    # BFS to assign (level, index_in_level)
    levels: list[list[str]] = []
    queue: list[tuple[str, int]] = [(start_id, 0)]
    visited: set[str] = set()

    while queue:
        node_id, level = queue.pop(0)
        if node_id in visited or node_id not in node_map:
            continue
        visited.add(node_id)

        while len(levels) <= level:
            levels.append([])
        levels[level].append(node_id)

        for child_id in connections.get(node_id, []):
            if child_id not in visited:
                queue.append((child_id, level + 1))

    # Assign positions based on level structure
    for level_idx, level_nodes in enumerate(levels):
        level_width = len(level_nodes) * X_SPACING
        start_x = START_X - level_width // 2 + X_SPACING // 2

        for node_idx, node_id in enumerate(level_nodes):
            if node_id in node_map:
                node_map[node_id]["position"] = [
                    start_x + node_idx * X_SPACING,
                    START_Y + level_idx * Y_SPACING,
                ]
                placed.add(node_id)

    # Place any unvisited nodes below the last level
    next_y = START_Y + len(levels) * Y_SPACING
    for node in nodes:
        if node["id"] not in placed:
            node["position"] = [START_X, next_y]
            next_y += Y_SPACING
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_layout.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/n8n/layout.py tests/test_layout.py
git commit -m "feat: add n8n node layout algorithm (tree-based BFS placement)"
```

---

### Task 8: n8n Mapper (Step → Node Conversion)

**Files:**
- Create: `src/cx_task_harness/n8n/mapper.py`
- Modify: `src/cx_task_harness/n8n/__init__.py`
- Create: `tests/test_mapper.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_mapper.py
"""Tests for TaskSpec step → n8n node mapper."""

from cx_task_harness.models.task_spec import TaskSpec


class TestMapper:
    def test_map_minimal(self, minimal_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec

        spec = TaskSpec(**minimal_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=False)
        assert "nodes" in result
        assert "connections" in result
        assert "setup_required" in result
        # At least: trigger + set (memory init) + the one message step
        assert len(result["nodes"]) >= 2

    def test_map_order_cancel(self, order_cancel_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec

        spec = TaskSpec(**order_cancel_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=False)
        node_names = [n["name"] for n in result["nodes"]]
        # Should have function steps mapped to HTTP Request
        assert any("n8n-nodes-base.httpRequest" in n["type"] for n in result["nodes"])
        # Should have branch step mapped to IF
        assert any("n8n-nodes-base.if" in n["type"] for n in result["nodes"])
        # Setup required for function steps
        assert len(result["setup_required"]) > 0

    def test_mock_data_insertion(self, order_cancel_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec

        spec = TaskSpec(**order_cancel_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=True)
        # Mock nodes should be inserted
        mock_nodes = [n for n in result["nodes"] if "[Mock]" in n["name"]]
        assert len(mock_nodes) > 0

    def test_connections_reference_valid_nodes(self, order_cancel_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec

        spec = TaskSpec(**order_cancel_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=False)
        node_ids = {n["id"] for n in result["nodes"]}
        for source_id, targets in result["connections"].items():
            assert source_id in node_ids, f"Source {source_id} not in nodes"
            for target_id in targets:
                assert target_id in node_ids, f"Target {target_id} not in nodes"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mapper.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement mapper**

```python
# src/cx_task_harness/n8n/mapper.py
"""Map TaskSpec steps to n8n nodes."""

from __future__ import annotations

from cx_task_harness.models.n8n import SetupItem
from cx_task_harness.models.steps import (
    ActionStep,
    AgentStep,
    BranchStep,
    BrowserStep,
    CodeStep,
    FunctionStep,
    MessageStep,
)
from cx_task_harness.models.task_spec import TaskSpec
from cx_task_harness.n8n.node_templates import (
    make_ai_agent_node,
    make_code_node,
    make_http_request_node,
    make_if_node,
    make_manual_trigger,
    make_mock_response_node,
    make_set_node,
)


def map_task_spec(
    spec: TaskSpec,
    include_mock_data: bool = True,
) -> dict:
    """Convert a TaskSpec to n8n nodes, connections, and setup requirements.

    Returns: {"nodes": [...], "connections": {src: [dst, ...]}, "setup_required": [...]}
    """
    nodes: list[dict] = []
    connections: dict[str, list[str]] = {}
    setup_required: list[dict] = []

    # 1. Trigger node
    trigger = make_manual_trigger(node_id="trigger")
    nodes.append(trigger)

    # 2. Memory initialization (Set node)
    if spec.memory:
        assignments = {m.key: "" for m in spec.memory}
        mem_node = make_set_node("init_memory", "Initialize Memory", assignments)
        nodes.append(mem_node)
        connections["trigger"] = ["init_memory"]
        first_connection_source = "init_memory"
    else:
        first_connection_source = "trigger"

    # 3. Map each step
    step_node_ids: dict[str, str] = {}  # step.id → n8n node id

    for step in spec.steps:
        node_id = f"step_{step.id}"
        step_node_ids[step.id] = node_id

        if isinstance(step, AgentStep):
            system_msg = _build_agent_system_message(step)
            node = make_ai_agent_node(node_id, step.name, system_msg)
            nodes.append(node)

        elif isinstance(step, CodeStep):
            node = make_code_node(node_id, step.name, step.code, step.language)
            nodes.append(node)

        elif isinstance(step, MessageStep):
            node = make_set_node(
                node_id, step.name, {"response": step.message_content}
            )
            nodes.append(node)

        elif isinstance(step, ActionStep):
            node = make_set_node(
                node_id,
                step.name,
                {"action": step.action_type, **{str(k): str(v) for k, v in step.action_params.items()}},
            )
            nodes.append(node)

        elif isinstance(step, FunctionStep):
            node = make_http_request_node(
                node_id,
                step.name,
                url=step.function_url,
                method=step.function_method,
                headers=step.function_headers or None,
                body=step.function_body,
            )
            nodes.append(node)

            setup_required.append(
                SetupItem(
                    node_id=node_id,
                    node_name=step.name,
                    type="credential",
                    description=f"Configure {step.function_method} {step.function_url}",
                    fields=["url", "authentication"],
                ).model_dump()
            )

            if include_mock_data:
                mock_id = f"mock_{step.id}"
                mock_node = make_mock_response_node(
                    mock_id, step.name, {"status": "ok", "mock": True}
                )
                nodes.append(mock_node)
                step_node_ids[f"_mock_{step.id}"] = mock_id

        elif isinstance(step, BranchStep):
            conditions = []
            for branch in step.branches:
                conditions.append({
                    "variable": branch.variable or "value",
                    "operator": branch.operator or "eq",
                    "value": branch.value or "",
                })
            node = make_if_node(node_id, step.name, conditions)
            nodes.append(node)

        elif isinstance(step, BrowserStep):
            # Placeholder: HTTP Request pointing to the URL
            node = make_http_request_node(
                node_id, f"[Browser] {step.name}", url=step.url, method="GET"
            )
            nodes.append(node)
            setup_required.append(
                SetupItem(
                    node_id=node_id,
                    node_name=step.name,
                    type="config",
                    description="Browser automation step — requires manual n8n configuration",
                    fields=["url", "actions"],
                ).model_dump()
            )

    # 4. Build connections from step references
    # Connect first step to memory init (or trigger)
    if spec.steps:
        first_step_node = step_node_ids[spec.steps[0].id]
        connections.setdefault(first_connection_source, []).append(first_step_node)

    for step in spec.steps:
        src = step_node_ids[step.id]

        if isinstance(step, BranchStep):
            for branch in step.branches:
                if branch.next_step in step_node_ids:
                    connections.setdefault(src, []).append(step_node_ids[branch.next_step])
            if step.default_branch and step.default_branch in step_node_ids:
                connections.setdefault(src, []).append(step_node_ids[step.default_branch])
        else:
            if step.next_step and step.next_step in step_node_ids:
                connections.setdefault(src, []).append(step_node_ids[step.next_step])

        if step.on_failure and step.on_failure in step_node_ids:
            connections.setdefault(src, []).append(step_node_ids[step.on_failure])

    return {
        "nodes": nodes,
        "connections": connections,
        "setup_required": setup_required,
    }


def _build_agent_system_message(step: AgentStep) -> str:
    """Build a system message string from AgentInstruction."""
    inst = step.instructions
    parts = [f"Role: {inst.role}", "", "Conversation Flow:"]
    for i, flow in enumerate(inst.conversation_flow, 1):
        parts.append(f"{i}. {flow}")
    parts.extend(["", "Exit Conditions:"])
    for cond in inst.exit_conditions:
        parts.append(f"- {cond}")
    if inst.exceptions:
        parts.extend(["", "Exceptions:"])
        for exc in inst.exceptions:
            parts.append(f"- {exc}")
    return "\n".join(parts)
```

- [ ] **Step 4: Update n8n/__init__.py**

```python
# src/cx_task_harness/n8n/__init__.py
"""n8n conversion utilities."""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_mapper.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/cx_task_harness/n8n/ tests/test_mapper.py
git commit -m "feat: add TaskSpec → n8n node mapper with mock data support"
```

---

### Task 9: convert_to_n8n Tool

**Files:**
- Create: `src/cx_task_harness/tools/converter.py`
- Create: `tests/test_converter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_converter.py
"""Tests for convert_to_n8n tool."""

import json


class TestConvertToN8n:
    def test_convert_minimal(self, minimal_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n

        result = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        assert "workflow" in result
        assert "setup_required" in result
        wf = result["workflow"]
        assert "nodes" in wf
        assert "connections" in wf
        assert wf["name"] == "Test Task"

    def test_convert_order_cancel(self, order_cancel_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n

        result = convert_to_n8n(json.dumps(order_cancel_task_spec_dict))
        wf = result["workflow"]
        assert wf["name"] == "Order Cancellation"
        # Verify it's valid JSON by round-tripping
        json_str = json.dumps(wf)
        parsed = json.loads(json_str)
        assert parsed["name"] == "Order Cancellation"

    def test_nodes_have_positions(self, minimal_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n

        result = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        for node in result["workflow"]["nodes"]:
            assert "position" in node
            assert len(node["position"]) == 2
            assert isinstance(node["position"][0], int)

    def test_invalid_json_returns_error(self):
        from cx_task_harness.tools.converter import convert_to_n8n

        result = convert_to_n8n("not json")
        assert "error" in result

    def test_n8n_connections_format(self, minimal_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n

        result = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        wf = result["workflow"]
        # n8n connections should be in proper format
        assert "connections" in wf
        assert isinstance(wf["connections"], dict)

    def test_include_mock_data_flag(self, order_cancel_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n

        result_with_mock = convert_to_n8n(
            json.dumps(order_cancel_task_spec_dict), include_mock_data=True
        )
        result_no_mock = convert_to_n8n(
            json.dumps(order_cancel_task_spec_dict), include_mock_data=False
        )
        assert len(result_with_mock["workflow"]["nodes"]) > len(
            result_no_mock["workflow"]["nodes"]
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_converter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement converter**

```python
# src/cx_task_harness/tools/converter.py
"""convert_to_n8n tool implementation."""

from __future__ import annotations

import json as json_module

from pydantic import ValidationError

from cx_task_harness.models.task_spec import TaskSpec
from cx_task_harness.n8n.layout import compute_layout
from cx_task_harness.n8n.mapper import map_task_spec


def convert_to_n8n(
    task_spec: str,
    include_mock_data: bool = True,
    target_n8n_version: str = "1.x",
) -> dict:
    """Convert a TaskSpec JSON string to an n8n workflow.

    Returns {"workflow": dict, "setup_required": list[dict]}
    or {"error": str} on failure.
    """
    try:
        data = json_module.loads(task_spec)
    except json_module.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    try:
        spec = TaskSpec(**data)
    except ValidationError as e:
        return {"error": f"Invalid TaskSpec: {e}"}

    # Map steps to n8n nodes
    map_result = map_task_spec(spec, include_mock_data=include_mock_data)

    # Compute layout
    compute_layout(
        map_result["nodes"],
        map_result["connections"],
        start_id="trigger",
    )

    # Build n8n workflow JSON format
    n8n_connections = _build_n8n_connections(
        map_result["nodes"], map_result["connections"]
    )

    workflow = {
        "name": spec.name,
        "nodes": map_result["nodes"],
        "connections": n8n_connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
        },
        "tags": [],
        "meta": {
            "generatedBy": "cx-task-harness",
            "taskSpecId": spec.id,
            "targetN8nVersion": target_n8n_version,
        },
    }

    return {
        "workflow": workflow,
        "setup_required": map_result["setup_required"],
    }


def _build_n8n_connections(
    nodes: list[dict], connections: dict[str, list[str]]
) -> dict:
    """Convert adjacency map to n8n connections format.

    n8n format:
    {
        "NodeName": {
            "main": [
                [{"node": "TargetName", "type": "main", "index": 0}]
            ]
        }
    }
    """
    node_name_by_id = {n["id"]: n["name"] for n in nodes}
    n8n_conns: dict = {}

    for src_id, target_ids in connections.items():
        src_name = node_name_by_id.get(src_id, src_id)
        outputs: list[list[dict]] = []

        for target_id in target_ids:
            target_name = node_name_by_id.get(target_id, target_id)
            outputs.append([{"node": target_name, "type": "main", "index": 0}])

        if outputs:
            n8n_conns[src_name] = {"main": outputs}

    return n8n_conns
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_converter.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/tools/converter.py tests/test_converter.py
git commit -m "feat: add convert_to_n8n tool with layout and n8n connection format"
```

---

### Task 10: n8n JSON Schema & validate_n8n Tool

**Files:**
- Create: `tests/schemas/n8n_workflow.schema.json`
- Create: `src/cx_task_harness/tools/n8n_validator.py`
- Create: `tests/test_n8n_validator.py`

- [ ] **Step 1: Create a minimal n8n workflow JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "n8n Workflow",
  "description": "Minimal schema for n8n workflow validation (target: n8n 1.x)",
  "type": "object",
  "required": ["name", "nodes", "connections"],
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "type", "position", "parameters"],
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "type": {"type": "string"},
          "typeVersion": {"type": "integer", "minimum": 1},
          "position": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 2,
            "maxItems": 2
          },
          "parameters": {"type": "object"}
        }
      }
    },
    "connections": {"type": "object"},
    "active": {"type": "boolean"},
    "settings": {"type": "object"},
    "tags": {"type": "array"},
    "meta": {"type": "object"}
  }
}
```

Save to: `tests/schemas/n8n_workflow.schema.json`

- [ ] **Step 2: Write failing tests**

```python
# tests/test_n8n_validator.py
"""Tests for validate_n8n tool."""

import json


class TestValidateN8n:
    def test_valid_workflow(self, minimal_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n
        from cx_task_harness.tools.n8n_validator import validate_n8n

        result = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        wf_json = json.dumps(result["workflow"])
        validation = validate_n8n(wf_json)
        assert validation["valid"] is True
        assert validation["errors"] == []

    def test_invalid_json(self):
        from cx_task_harness.tools.n8n_validator import validate_n8n

        result = validate_n8n("not json")
        assert result["valid"] is False

    def test_missing_nodes(self):
        from cx_task_harness.tools.n8n_validator import validate_n8n

        result = validate_n8n(json.dumps({"name": "Test", "connections": {}}))
        assert result["valid"] is False

    def test_invalid_node_missing_position(self):
        from cx_task_harness.tools.n8n_validator import validate_n8n

        wf = {
            "name": "Test",
            "nodes": [{"id": "1", "name": "N", "type": "t", "parameters": {}}],
            "connections": {},
        }
        result = validate_n8n(json.dumps(wf))
        assert result["valid"] is False

    def test_returns_n8n_version(self, minimal_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n
        from cx_task_harness.tools.n8n_validator import validate_n8n

        result = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        validation = validate_n8n(json.dumps(result["workflow"]))
        assert "n8n_version" in validation
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_n8n_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement n8n validator**

```python
# src/cx_task_harness/tools/n8n_validator.py
"""validate_n8n tool implementation."""

from __future__ import annotations

import json as json_module
from pathlib import Path

import jsonschema


_SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "schemas" / "n8n_workflow.schema.json"
_BUNDLED_SCHEMA_PATH = Path(__file__).parent.parent / "_schemas" / "n8n_workflow.schema.json"

_N8N_TARGET_VERSION = "1.x"


def _load_schema() -> dict:
    """Load n8n workflow JSON Schema."""
    # Try bundled schema first, then test schema
    for path in [_BUNDLED_SCHEMA_PATH, _SCHEMA_PATH]:
        if path.exists():
            return json_module.loads(path.read_text())
    raise FileNotFoundError("n8n workflow schema not found")


def validate_n8n(workflow: str) -> dict:
    """Validate an n8n workflow JSON string against the schema.

    Returns {"valid": bool, "errors": list[str], "n8n_version": str}.
    """
    try:
        data = json_module.loads(workflow)
    except json_module.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "n8n_version": _N8N_TARGET_VERSION}

    try:
        schema = _load_schema()
    except FileNotFoundError:
        return {
            "valid": False,
            "errors": ["n8n workflow schema file not found"],
            "n8n_version": _N8N_TARGET_VERSION,
        }

    errors: list[str] = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(data):
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"{path}: {error.message}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "n8n_version": _N8N_TARGET_VERSION,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_n8n_validator.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add tests/schemas/ src/cx_task_harness/tools/n8n_validator.py tests/test_n8n_validator.py
git commit -m "feat: add validate_n8n tool with JSON Schema validation"
```

---

### Task 11: First Template — ecommerce/order_cancel

**Files:**
- Create: `src/cx_task_harness/templates/ecommerce/order_cancel.en.json`
- Create: `src/cx_task_harness/templates/ecommerce/order_cancel.ko.json`
- Modify: `tests/test_converter.py` (add snapshot test)

- [ ] **Step 1: Write the English template**

Use the `order_cancel_task_spec_dict` fixture from conftest.py as the content, saved as JSON. The file is a complete TaskSpec JSON.

```json
{
  "id": "ecommerce-order-cancel",
  "name": "Order Cancellation & Refund",
  "description": "Handles customer order cancellation requests, checks order status, and processes refunds",
  "industry": "ecommerce",
  "locale": "en",
  "trigger": {
    "intent": "Customer wants to cancel an order",
    "keywords": ["cancel", "cancellation", "cancel order", "refund", "void order"]
  },
  "memory": [
    {"key": "order_id", "type": "string", "description": "The order ID to cancel"},
    {"key": "cancel_reason", "type": "string", "description": "Reason for cancellation"}
  ],
  "steps": [
    {
      "id": "greet_and_collect",
      "name": "Greet and Collect Order Info",
      "type": "agent",
      "instructions": {
        "role": "Friendly customer support agent handling order cancellations",
        "conversation_flow": [
          "Greet the customer warmly",
          "Ask for the order ID or order number",
          "Ask for the reason for cancellation",
          "Confirm the cancellation request with the customer"
        ],
        "exit_conditions": [
          "Order ID and cancellation reason are both collected and confirmed by customer"
        ],
        "exceptions": [
          "If customer does not know the order ID, ask for the email address to look it up",
          "If customer is upset, acknowledge their frustration before proceeding"
        ]
      },
      "next_step": "check_order"
    },
    {
      "id": "check_order",
      "name": "Check Order Status",
      "type": "function",
      "function_url": "https://api.example.com/orders/{{order_id}}",
      "function_method": "GET",
      "function_headers": {"Authorization": "Bearer {{api_key}}"},
      "next_step": "branch_cancelable",
      "on_failure": "error_handler"
    },
    {
      "id": "branch_cancelable",
      "name": "Check if Order is Cancelable",
      "type": "branch",
      "branches": [
        {
          "condition": "Order is still pending or processing",
          "variable": "order_status",
          "operator": "in",
          "value": "pending,processing",
          "next_step": "cancel_order"
        },
        {
          "condition": "Order has already been shipped",
          "variable": "order_status",
          "operator": "eq",
          "value": "shipped",
          "next_step": "shipped_message"
        }
      ],
      "default_branch": "error_handler"
    },
    {
      "id": "cancel_order",
      "name": "Execute Cancellation",
      "type": "function",
      "function_url": "https://api.example.com/orders/{{order_id}}/cancel",
      "function_method": "POST",
      "function_body": {"reason": "{{cancel_reason}}"},
      "next_step": "confirm_message",
      "on_failure": "error_handler"
    },
    {
      "id": "confirm_message",
      "name": "Confirm Cancellation",
      "type": "message",
      "message_content": "Your order {{order_id}} has been successfully cancelled. A refund will be processed within 3-5 business days.",
      "next_step": "close_action"
    },
    {
      "id": "shipped_message",
      "name": "Already Shipped Notice",
      "type": "message",
      "message_content": "Your order {{order_id}} has already been shipped and cannot be cancelled. Would you like to initiate a return instead?",
      "next_step": "assign_to_human"
    },
    {
      "id": "close_action",
      "name": "Close Conversation",
      "type": "action",
      "action_type": "close",
      "action_params": {"tags": ["order-cancelled", "automated"]}
    },
    {
      "id": "assign_to_human",
      "name": "Assign to Human Agent",
      "type": "action",
      "action_type": "assign_team",
      "action_params": {"team": "returns-team"}
    },
    {
      "id": "error_handler",
      "name": "Error Handler",
      "type": "message",
      "message_content": "I'm sorry, I encountered an issue processing your request. Let me connect you with a human agent who can help.",
      "next_step": "assign_to_human"
    }
  ],
  "automation_potential": {
    "score": 0.92,
    "reasoning": "Order cancellation is a highly repetitive, rule-based process with clear decision points",
    "estimated_resolution_rate": 0.80
  }
}
```

Save to: `src/cx_task_harness/templates/ecommerce/order_cancel.en.json`

- [ ] **Step 2: Write the Korean template**

```json
{
  "id": "ecommerce-order-cancel",
  "name": "주문 취소 및 환불",
  "description": "고객의 주문 취소 요청을 처리하고, 주문 상태를 확인한 후 환불을 진행합니다",
  "industry": "ecommerce",
  "locale": "ko",
  "trigger": {
    "intent": "고객이 주문을 취소하고 싶어합니다",
    "keywords": ["취소", "주문취소", "환불", "주문 취소해주세요", "캔슬"]
  },
  "memory": [
    {"key": "order_id", "type": "string", "description": "취소할 주문 번호"},
    {"key": "cancel_reason", "type": "string", "description": "취소 사유"}
  ],
  "steps": [
    {
      "id": "greet_and_collect",
      "name": "인사 및 주문 정보 수집",
      "type": "agent",
      "instructions": {
        "role": "친절한 고객 상담 에이전트 (주문 취소 담당)",
        "conversation_flow": [
          "고객에게 친절하게 인사합니다",
          "주문 번호를 확인합니다",
          "취소 사유를 여쭤봅니다",
          "취소 요청을 고객과 최종 확인합니다"
        ],
        "exit_conditions": [
          "주문 번호와 취소 사유가 모두 수집되고 고객이 확인함"
        ],
        "exceptions": [
          "주문 번호를 모르는 경우, 이메일 주소로 조회를 안내합니다",
          "고객이 불만을 표현하는 경우, 먼저 공감한 후 진행합니다"
        ]
      },
      "next_step": "check_order"
    },
    {
      "id": "check_order",
      "name": "주문 상태 확인",
      "type": "function",
      "function_url": "https://api.example.com/orders/{{order_id}}",
      "function_method": "GET",
      "function_headers": {"Authorization": "Bearer {{api_key}}"},
      "next_step": "branch_cancelable",
      "on_failure": "error_handler"
    },
    {
      "id": "branch_cancelable",
      "name": "취소 가능 여부 확인",
      "type": "branch",
      "branches": [
        {
          "condition": "주문이 대기 중이거나 처리 중인 경우",
          "variable": "order_status",
          "operator": "in",
          "value": "pending,processing",
          "next_step": "cancel_order"
        },
        {
          "condition": "이미 배송된 경우",
          "variable": "order_status",
          "operator": "eq",
          "value": "shipped",
          "next_step": "shipped_message"
        }
      ],
      "default_branch": "error_handler"
    },
    {
      "id": "cancel_order",
      "name": "취소 실행",
      "type": "function",
      "function_url": "https://api.example.com/orders/{{order_id}}/cancel",
      "function_method": "POST",
      "function_body": {"reason": "{{cancel_reason}}"},
      "next_step": "confirm_message",
      "on_failure": "error_handler"
    },
    {
      "id": "confirm_message",
      "name": "취소 완료 안내",
      "type": "message",
      "message_content": "주문 {{order_id}}이(가) 성공적으로 취소되었습니다. 환불은 3~5 영업일 내에 처리됩니다.",
      "next_step": "close_action"
    },
    {
      "id": "shipped_message",
      "name": "배송 완료 안내",
      "type": "message",
      "message_content": "주문 {{order_id}}은(는) 이미 배송이 시작되어 취소가 불가합니다. 반품 절차를 안내해 드릴까요?",
      "next_step": "assign_to_human"
    },
    {
      "id": "close_action",
      "name": "상담 종료",
      "type": "action",
      "action_type": "close",
      "action_params": {"tags": ["주문취소", "자동처리"]}
    },
    {
      "id": "assign_to_human",
      "name": "상담원 연결",
      "type": "action",
      "action_type": "assign_team",
      "action_params": {"team": "반품팀"}
    },
    {
      "id": "error_handler",
      "name": "오류 처리",
      "type": "message",
      "message_content": "죄송합니다. 요청을 처리하는 중 문제가 발생했습니다. 상담원에게 연결해 드리겠습니다.",
      "next_step": "assign_to_human"
    }
  ],
  "automation_potential": {
    "score": 0.92,
    "reasoning": "주문 취소는 반복적이고 규칙 기반의 프로세스로, 명확한 분기점이 있어 자동화에 적합합니다",
    "estimated_resolution_rate": 0.80
  }
}
```

Save to: `src/cx_task_harness/templates/ecommerce/order_cancel.ko.json`

- [ ] **Step 3: Write end-to-end template test**

Append to `tests/test_converter.py`:

```python
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "src" / "cx_task_harness" / "templates"


class TestTemplateEndToEnd:
    """End-to-end: load template → validate → convert → validate n8n."""

    def test_order_cancel_en_pipeline(self):
        from cx_task_harness.tools.validator import validate_task_spec
        from cx_task_harness.tools.converter import convert_to_n8n
        from cx_task_harness.tools.n8n_validator import validate_n8n

        template_path = TEMPLATES_DIR / "ecommerce" / "order_cancel.en.json"
        task_spec_json = template_path.read_text()

        # 1. Validate TaskSpec
        v_result = validate_task_spec(task_spec_json)
        assert v_result["valid"], f"TaskSpec invalid: {v_result['errors']}"

        # 2. Convert to n8n
        c_result = convert_to_n8n(task_spec_json, include_mock_data=True)
        assert "error" not in c_result

        # 3. Validate n8n workflow
        n_result = validate_n8n(json.dumps(c_result["workflow"]))
        assert n_result["valid"], f"n8n invalid: {n_result['errors']}"

    def test_order_cancel_ko_pipeline(self):
        from cx_task_harness.tools.validator import validate_task_spec
        from cx_task_harness.tools.converter import convert_to_n8n
        from cx_task_harness.tools.n8n_validator import validate_n8n

        template_path = TEMPLATES_DIR / "ecommerce" / "order_cancel.ko.json"
        task_spec_json = template_path.read_text()

        v_result = validate_task_spec(task_spec_json)
        assert v_result["valid"], f"TaskSpec invalid: {v_result['errors']}"

        c_result = convert_to_n8n(task_spec_json, include_mock_data=True)
        assert "error" not in c_result

        n_result = validate_n8n(json.dumps(c_result["workflow"]))
        assert n_result["valid"], f"n8n invalid: {n_result['errors']}"

    def test_order_cancel_snapshot(self, snapshot):
        from cx_task_harness.tools.converter import convert_to_n8n

        template_path = TEMPLATES_DIR / "ecommerce" / "order_cancel.en.json"
        result = convert_to_n8n(template_path.read_text(), include_mock_data=False)
        # Snapshot the workflow structure (excluding positions which may change)
        wf = result["workflow"]
        node_summary = [{"id": n["id"], "type": n["type"], "name": n["name"]} for n in wf["nodes"]]
        assert node_summary == snapshot
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_converter.py -v --snapshot-update`
Expected: All tests PASS, snapshot created

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/templates/ecommerce/ tests/test_converter.py tests/snapshots/
git commit -m "feat: add ecommerce/order_cancel templates (en/ko) with end-to-end test"
```

---

### Task 12: list_templates Tool

**Files:**
- Create: `src/cx_task_harness/tools/templates.py`
- Create: `tests/test_templates.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_templates.py
"""Tests for list_templates tool."""


class TestListTemplates:
    def test_list_all(self):
        from cx_task_harness.tools.templates import list_templates

        result = list_templates()
        assert "templates" in result
        assert len(result["templates"]) >= 2  # At least en + ko for order_cancel

    def test_filter_by_industry(self):
        from cx_task_harness.tools.templates import list_templates

        result = list_templates(industry="ecommerce")
        for t in result["templates"]:
            assert t["industry"] == "ecommerce"

    def test_filter_by_locale(self):
        from cx_task_harness.tools.templates import list_templates

        result = list_templates(locale="ko")
        for t in result["templates"]:
            assert t["locale"] == "ko"

    def test_filter_by_industry_and_locale(self):
        from cx_task_harness.tools.templates import list_templates

        result = list_templates(industry="ecommerce", locale="en")
        for t in result["templates"]:
            assert t["industry"] == "ecommerce"
            assert t["locale"] == "en"

    def test_template_summary_fields(self):
        from cx_task_harness.tools.templates import list_templates

        result = list_templates(locale="en")
        if result["templates"]:
            t = result["templates"][0]
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "industry" in t
            assert "steps_count" in t
            assert "step_types" in t

    def test_all_templates_are_valid_task_specs(self):
        """Every template file should parse as a valid TaskSpec."""
        import json
        from cx_task_harness.tools.templates import list_templates, get_template
        from cx_task_harness.tools.validator import validate_task_spec

        result = list_templates()
        for t in result["templates"]:
            spec_json = get_template(t["id"], t["locale"])
            assert spec_json is not None, f"Template {t['id']} ({t['locale']}) not found"
            v = validate_task_spec(spec_json)
            assert v["valid"], f"Template {t['id']} ({t['locale']}) invalid: {v['errors']}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_templates.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement templates tool**

```python
# src/cx_task_harness/tools/templates.py
"""list_templates tool implementation."""

from __future__ import annotations

import json as json_module
from pathlib import Path

from cx_task_harness.models.task_spec import TaskSpec

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def list_templates(
    industry: str | None = None,
    locale: str = "en",
) -> dict:
    """List available industry templates.

    Returns {"templates": list[dict]}.
    """
    templates: list[dict] = []

    for json_file in sorted(_TEMPLATES_DIR.rglob("*.json")):
        try:
            data = json_module.loads(json_file.read_text())
            spec = TaskSpec(**data)
        except Exception:
            continue

        # Derive industry from directory name
        file_industry = json_file.parent.name

        # Filter
        if industry and file_industry != industry:
            continue
        if spec.locale != locale:
            continue

        # Build template ID from path
        template_id = f"{file_industry}/{json_file.stem.rsplit('.', 1)[0]}"
        step_types = list({s.type for s in spec.steps})

        templates.append({
            "id": template_id,
            "name": spec.name,
            "description": spec.description,
            "industry": file_industry,
            "locale": spec.locale,
            "steps_count": len(spec.steps),
            "step_types": sorted(step_types),
        })

    return {"templates": templates}


def get_template(template_id: str, locale: str = "en") -> str | None:
    """Load a template's full TaskSpec JSON by ID and locale.

    Args:
        template_id: e.g., "ecommerce/order_cancel"
        locale: "en" or "ko"

    Returns: JSON string or None if not found.
    """
    # template_id: "ecommerce/order_cancel" → "ecommerce/order_cancel.en.json"
    parts = template_id.split("/")
    if len(parts) != 2:
        return None

    file_path = _TEMPLATES_DIR / parts[0] / f"{parts[1]}.{locale}.json"
    if file_path.exists():
        return file_path.read_text()
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_templates.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cx_task_harness/tools/templates.py tests/test_templates.py
git commit -m "feat: add list_templates tool with industry/locale filtering"
```

---

### Task 13: MCP Server (FastMCP)

**Files:**
- Create: `src/cx_task_harness/server.py`
- Modify: `src/cx_task_harness/tools/__init__.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_server.py
"""Integration tests for MCP server."""

import json
import pytest
from cx_task_harness.server import mcp


class TestServerTools:
    @pytest.mark.asyncio
    async def test_validate_task_spec_tool(self, minimal_task_spec_dict):
        result = await mcp.call_tool(
            "validate_task_spec",
            {"task_spec": json.dumps(minimal_task_spec_dict)},
        )
        # FastMCP returns list of content blocks
        assert len(result) > 0
        data = json.loads(result[0].text)
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_convert_to_n8n_tool(self, minimal_task_spec_dict):
        result = await mcp.call_tool(
            "convert_to_n8n",
            {"task_spec": json.dumps(minimal_task_spec_dict)},
        )
        data = json.loads(result[0].text)
        assert "workflow" in data

    @pytest.mark.asyncio
    async def test_validate_n8n_tool(self, minimal_task_spec_dict):
        # First convert, then validate the output
        convert_result = await mcp.call_tool(
            "convert_to_n8n",
            {"task_spec": json.dumps(minimal_task_spec_dict)},
        )
        workflow = json.loads(convert_result[0].text)["workflow"]
        result = await mcp.call_tool(
            "validate_n8n",
            {"workflow": json.dumps(workflow)},
        )
        data = json.loads(result[0].text)
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_list_templates_tool(self):
        result = await mcp.call_tool("list_templates", {"locale": "en"})
        data = json.loads(result[0].text)
        assert "templates" in data
        assert len(data["templates"]) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement server**

```python
# src/cx_task_harness/server.py
"""CX Task Harness — FastMCP server."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from cx_task_harness.tools.converter import convert_to_n8n as _convert_to_n8n
from cx_task_harness.tools.n8n_validator import validate_n8n as _validate_n8n
from cx_task_harness.tools.templates import get_template, list_templates as _list_templates
from cx_task_harness.tools.validator import validate_task_spec as _validate_task_spec

mcp = FastMCP(
    "cx-task-harness",
    description="Validates CX Task Specs and converts them to n8n workflows",
)


@mcp.tool()
def validate_task_spec(task_spec: str) -> str:
    """Validate a CX Task Spec JSON for structural integrity.

    Checks: Pydantic schema, step references, circular dependencies,
    branch targets, agent exit conditions, memory key uniqueness.
    Returns warnings for unreachable steps and missing error handlers.

    Args:
        task_spec: Complete TaskSpec as a JSON string.
    """
    result = _validate_task_spec(task_spec)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def convert_to_n8n(
    task_spec: str,
    include_mock_data: bool = True,
    target_n8n_version: str = "1.x",
) -> str:
    """Convert a CX Task Spec to an importable n8n workflow JSON.

    Maps each step type to corresponding n8n nodes. Generates node
    positions, connections, and a list of items requiring manual setup
    (API keys, endpoints, etc.).

    Args:
        task_spec: Validated TaskSpec as a JSON string.
        include_mock_data: Insert mock response nodes for API steps (default: true).
        target_n8n_version: Target n8n version for compatibility (default: "1.x").
    """
    result = _convert_to_n8n(task_spec, include_mock_data, target_n8n_version)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def validate_n8n(workflow: str) -> str:
    """Validate an n8n workflow JSON against the n8n schema.

    Checks node structure, required fields, position format,
    and connection reference integrity.

    Args:
        workflow: n8n workflow as a JSON string.
    """
    result = _validate_n8n(workflow)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def list_templates(
    industry: str | None = None,
    locale: str = "en",
) -> str:
    """List available industry task spec templates.

    Returns template summaries with ID, name, description, step count,
    and step types. Use the template ID to load the full spec via resources.

    Args:
        industry: Filter by industry (e.g., "ecommerce", "travel"). Omit for all.
        locale: Language locale — "en" or "ko" (default: "en").
    """
    result = _list_templates(industry=industry, locale=locale)
    return json.dumps(result, ensure_ascii=False)


# ── Resources ──────────────────────────────────────────

@mcp.resource("template://{template_id}/{locale}")
def read_template(template_id: str, locale: str = "en") -> str:
    """Read a full TaskSpec template by ID and locale.

    Example URI: template://ecommerce/order_cancel/en
    """
    content = get_template(template_id, locale)
    if content is None:
        return json.dumps({"error": f"Template '{template_id}' ({locale}) not found"})
    return content
```

- [ ] **Step 4: Update tools/__init__.py**

```python
# src/cx_task_harness/tools/__init__.py
"""Tool implementations."""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_server.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/cx_task_harness/server.py src/cx_task_harness/tools/__init__.py tests/test_server.py
git commit -m "feat: add FastMCP server with all tools and template resources"
```

---

### Task 14: Remaining Templates (7 templates × 2 locales)

**Files:**
- Create: 14 template JSON files in `src/cx_task_harness/templates/`

This task creates the remaining 7 templates in both English and Korean. Each template follows the same structure as `order_cancel` — a complete TaskSpec JSON with realistic steps for that use case.

**Templates to create:**

1. `ecommerce/exchange_return.{en,ko}.json` — Exchange & return processing
2. `ecommerce/delivery_tracking.{en,ko}.json` — Delivery status inquiry
3. `ecommerce/size_stock_check.{en,ko}.json` — Size & stock availability
4. `travel/reservation_change.{en,ko}.json` — Reservation modification
5. `travel/reservation_cancel.{en,ko}.json` — Reservation cancellation
6. `saas/subscription_manage.{en,ko}.json` — Subscription change & cancellation
7. `medical/appointment_change.{en,ko}.json` — Appointment rescheduling

- [ ] **Step 1: Create ecommerce/exchange_return templates**

Each template must:
- Be a valid TaskSpec (parseable by Pydantic)
- Have at least one AgentStep with exit_conditions
- Use realistic step types for the scenario (agent, function, branch, message, action)
- Have `on_failure` on FunctionStep/CodeStep
- Not have circular references or broken step references

Write the English version, then the Korean version with translated user-facing text but identical structure.

- [ ] **Step 2: Create ecommerce/delivery_tracking templates**
- [ ] **Step 3: Create ecommerce/size_stock_check templates**
- [ ] **Step 4: Create travel/reservation_change templates**
- [ ] **Step 5: Create travel/reservation_cancel templates**
- [ ] **Step 6: Create saas/subscription_manage templates**
- [ ] **Step 7: Create medical/appointment_change templates**

- [ ] **Step 8: Run all template validation tests**

Run: `uv run pytest tests/test_templates.py -v`
Expected: All tests PASS — every template parses and validates

- [ ] **Step 9: Run full pipeline test on all templates**

Add to `tests/test_templates.py`:

```python
class TestAllTemplatesPipeline:
    """Verify every template passes the full pipeline."""

    def test_all_templates_convert_and_validate(self):
        import json
        from cx_task_harness.tools.templates import list_templates, get_template
        from cx_task_harness.tools.validator import validate_task_spec
        from cx_task_harness.tools.converter import convert_to_n8n
        from cx_task_harness.tools.n8n_validator import validate_n8n

        for locale in ["en", "ko"]:
            result = list_templates(locale=locale)
            assert len(result["templates"]) == 8, f"Expected 8 {locale} templates"

            for t in result["templates"]:
                spec_json = get_template(t["id"], locale)
                assert spec_json is not None

                v = validate_task_spec(spec_json)
                assert v["valid"], f"{t['id']} ({locale}) invalid: {v['errors']}"

                c = convert_to_n8n(spec_json)
                assert "error" not in c, f"{t['id']} ({locale}) convert error: {c.get('error')}"

                n = validate_n8n(json.dumps(c["workflow"]))
                assert n["valid"], f"{t['id']} ({locale}) n8n invalid: {n['errors']}"
```

Run: `uv run pytest tests/test_templates.py::TestAllTemplatesPipeline -v`
Expected: PASS — all 16 templates pass full pipeline

- [ ] **Step 10: Commit**

```bash
git add src/cx_task_harness/templates/ tests/test_templates.py
git commit -m "feat: add all industry templates (8 templates × 2 locales)"
```

---

### Task 15: Claude Code Native — CLAUDE.md & Slash Commands

**Files:**
- Create: `claude/CLAUDE.md`
- Create: `claude/commands/analyze.md`
- Create: `claude/commands/design.md`
- Create: `claude/commands/guide.md`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# CX Task Harness — Workflow Guide

## MCP Tools Available

- `validate_task_spec` — Validate a TaskSpec JSON (run after generating)
- `convert_to_n8n` — Convert TaskSpec to n8n workflow JSON
- `validate_n8n` — Validate n8n workflow JSON against schema
- `list_templates` — Browse industry task templates

## Pipeline Rules

1. Always **validate** a TaskSpec before converting to n8n
2. Always **validate** the n8n output after conversion
3. Use `list_templates` to check for existing templates before designing from scratch
4. When using `/design`, auto-fix and re-validate if validation fails

## TaskSpec Authoring Guidelines

- All step IDs must be unique and use snake_case (e.g., `check_order_status`)
- AgentStep must have at least one `exit_conditions` entry
- FunctionStep and CodeStep should have `on_failure` set
- Memory variables: only declare what is actually used in steps
- Avoid circular step references

## Supported Industries

ecommerce, travel, saas, medical — run `list_templates` for full catalog
```

- [ ] **Step 2: Create /analyze command**

```markdown
You are a customer support data analyst. Your job is to analyze support conversation logs and identify patterns that can be automated.

## Input

The user will provide a path to a CSV or JSON file containing support logs. Expected columns: timestamp, customer_message, agent_response, resolution_type, tags (optional).

## Process

1. Read the data file
2. Cluster messages by customer intent (group similar requests)
3. For each cluster, determine:
   - Frequency (how many conversations)
   - Representative sample messages (3 examples)
   - Automation potential score (0-1):
     - 0.8-1.0: Simple, rule-based, repetitive (order status, cancellation)
     - 0.5-0.8: Moderate complexity, some judgment needed (exchanges, returns)
     - 0.0-0.5: Complex, emotional, requires human empathy
4. Check `list_templates` to see if matching templates exist for the identified patterns

## Output Format

Provide a structured report:
- **Total conversations analyzed:** N
- **Intent clusters** (sorted by frequency):
  For each cluster:
  - Intent name
  - Frequency and percentage
  - 3 sample messages
  - Automation score with brief reasoning
  - Matching template (if available)
- **Recommended automation tasks** (priority ordered)
- **Estimated overall automation rate**
```

- [ ] **Step 3: Create /design command**

```markdown
You are a CX automation designer. Your job is to create a CX Task Spec from a natural language scenario description.

## Input

The user describes an automation scenario in natural language (e.g., "Handle order cancellation for an ecommerce store").

## Process

1. Check `list_templates` — if a matching template exists, load it as a starting point
2. Read the task-spec-schema resource to understand the required structure
3. Design the TaskSpec:
   - Define a clear trigger with intent and keywords
   - Map out the conversation/workflow steps
   - Identify where branches are needed (decision points)
   - Determine which external APIs need to be called (FunctionStep)
   - Define memory variables for data that flows between steps
   - Set up error handling (on_failure paths)
4. Generate the complete TaskSpec JSON
5. Run `validate_task_spec` on the result
6. If validation fails, fix the issues and re-validate
7. Present the validated TaskSpec to the user

## Output

- The validated TaskSpec JSON
- A brief explanation of the design decisions
- Any assumptions made about external APIs or business logic

## Guidelines

- Every AgentStep needs at least one exit_conditions
- Every FunctionStep and CodeStep should have on_failure
- Use snake_case for step IDs
- Keep agent instructions clear and specific
- Include realistic exception handling in agent steps
```

- [ ] **Step 4: Create /guide command**

```markdown
You are an n8n workflow setup consultant. Your job is to generate a clear setup guide for an n8n workflow that was converted from a CX Task Spec.

## Input

The user has just run `convert_to_n8n` and has a workflow JSON and setup_required list.

## Process

1. Analyze the `setup_required` items from the conversion result
2. For each item, generate specific setup instructions
3. Categorize nodes into "Ready to run" and "Requires manual setup"
4. For manual setup items, provide:
   - Which n8n node to configure
   - What credentials or endpoints are needed
   - Step-by-step instructions for configuration
   - Example values where helpful

## Output Format

# n8n Workflow Setup Guide

## Ready to Run
These nodes work out of the box (or with mock data):
- [ ] Node 1 — description
- [ ] Node 2 — description

## Manual Setup Required
Configure these nodes before running in production:

### 1. [Node Name]
- **Node type:** HTTP Request
- **What to configure:** API endpoint and authentication
- **Steps:**
  1. Open the node in n8n
  2. Set the URL to your actual API endpoint
  3. Add authentication credentials
- **Example:** `https://your-api.com/orders/{order_id}`

### 2. [Next Node]
...

## Testing Checklist
- [ ] Import workflow into n8n
- [ ] Run with mock data first
- [ ] Configure each manual setup item
- [ ] Test with real data
- [ ] Verify error handling paths
```

- [ ] **Step 5: Commit**

```bash
git add claude/
git commit -m "feat: add Claude Code CLAUDE.md and slash commands (analyze, design, guide)"
```

---

### Task 16: Sample Fixture & README

**Files:**
- Create: `tests/fixtures/sample_support_logs.csv`
- Create: `README.md`
- Create: `docs/TASK_SPEC.md`

- [ ] **Step 1: Create sample support logs fixture**

```csv
timestamp,customer_message,agent_response,resolution_type,tags
2026-01-15 09:30:00,"I want to cancel my order #12345","Sure, I can help with that. Let me look up your order.","resolved","order-cancel"
2026-01-15 10:15:00,"Where is my package? Order #12346","Let me check the tracking for you. It shows your package is in transit.","resolved","delivery-tracking"
2026-01-15 10:45:00,"I need to cancel order #12347","I've processed the cancellation. You'll receive a refund in 3-5 days.","resolved","order-cancel"
2026-01-15 11:00:00,"Can I exchange this for a different size?","Of course! What size would you like instead?","resolved","exchange"
2026-01-15 11:30:00,"Cancel my order please, order number 12348","Done! Your order has been cancelled and refund initiated.","resolved","order-cancel"
2026-01-15 12:00:00,"My delivery is late, order #12349","I apologize for the delay. Let me check the status.","resolved","delivery-tracking"
2026-01-15 12:30:00,"I want to return this item","I'd be happy to help with the return. Could you share your order number?","resolved","return"
2026-01-15 13:00:00,"Please cancel order #12350","Cancellation processed. Refund will appear in 3-5 business days.","resolved","order-cancel"
2026-01-15 13:30:00,"Do you have this in size M?","Let me check stock for you. Yes, size M is available!","resolved","stock-check"
2026-01-15 14:00:00,"I need to cancel my recent order","Could you please provide the order number?","resolved","order-cancel"
```

Save to: `tests/fixtures/sample_support_logs.csv`

- [ ] **Step 2: Create README.md**

```markdown
# cx-task-harness

An MCP server plugin for Claude Code that validates CX Task Specs and converts them to n8n workflows.

## What it does

1. **Validate** automation task specs against a strict schema
2. **Convert** specs to importable n8n workflow JSON
3. **Browse** industry-specific templates (ecommerce, travel, SaaS, medical)
4. **Guide** the setup of converted workflows

## Quick Start

### Install

```bash
# Add as MCP server to Claude Code
claude mcp add cx-task-harness \
  -- uv run --with fastmcp --with pydantic --with jsonschema \
  fastmcp run src/cx_task_harness/server.py
```

### Copy Claude Code files

Copy the `claude/` directory contents to your project:
- `claude/CLAUDE.md` → your project's `CLAUDE.md` (merge if exists)
- `claude/commands/` → your project's `.claude/commands/`

### Use

In Claude Code:

```
> /analyze path/to/support_logs.csv
> /design "Handle order cancellation for an ecommerce store"
> /guide
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `validate_task_spec` | Validate TaskSpec JSON structure |
| `convert_to_n8n` | Convert TaskSpec → n8n workflow |
| `validate_n8n` | Validate n8n workflow JSON |
| `list_templates` | Browse industry templates |

## Templates

8 templates in English and Korean:

- **ecommerce:** order cancel, exchange/return, delivery tracking, size/stock check
- **travel:** reservation change, reservation cancel
- **saas:** subscription management
- **medical:** appointment change

## Development

```bash
uv sync --dev
uv run pytest -v
```

## License

MIT
```

- [ ] **Step 3: Create TASK_SPEC.md reference**

```markdown
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

See the design spec for full field definitions.
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/ README.md docs/TASK_SPEC.md
git commit -m "docs: add README, TASK_SPEC reference, and sample fixture"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - [x] TaskSpec schema (Discriminated Union) — Tasks 2-4
   - [x] validate_task_spec — Task 5
   - [x] convert_to_n8n — Tasks 6-9
   - [x] validate_n8n — Task 10
   - [x] list_templates — Task 12
   - [x] Templates (8 × 2 locales) — Tasks 11, 14
   - [x] MCP server — Task 13
   - [x] Claude Code native (CLAUDE.md, commands) — Task 15
   - [x] Testing (unit, snapshot, schema, integration) — throughout
   - [x] README & docs — Task 16

2. **Placeholder scan:** No TBD/TODO found. All code blocks complete.

3. **Type consistency:**
   - `validate_task_spec` returns `dict` with `valid`, `errors`, `warnings` — consistent across Task 5 and 13
   - `convert_to_n8n` returns `dict` with `workflow`, `setup_required` — consistent across Tasks 9 and 13
   - `Step` union type used consistently from Task 3 onward
   - `SetupItem` model from Task 4, used in mapper (Task 8) and converter (Task 9)
