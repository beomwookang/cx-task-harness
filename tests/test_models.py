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

        step = CodeStep(id="validate", name="Validate Input", code="return items.length > 0;")
        assert step.type == "code"
        assert step.language == "javascript"

    def test_code_step_python(self):
        from cx_task_harness.models.steps import CodeStep

        step = CodeStep(id="validate", name="Validate", code="return len(items) > 0", language="python")
        assert step.language == "python"

    def test_message_step(self):
        from cx_task_harness.models.steps import MessageStep

        step = MessageStep(id="msg", name="Send Message", message_content="Hello!")
        assert step.type == "message"

    def test_action_step(self):
        from cx_task_harness.models.steps import ActionStep

        step = ActionStep(id="close", name="Close", action_type="close", action_params={"tags": ["done"]})
        assert step.type == "action"
        assert step.action_params == {"tags": ["done"]}

    def test_function_step(self):
        from cx_task_harness.models.steps import FunctionStep

        step = FunctionStep(id="api_call", name="Call API", function_url="https://api.example.com/orders", function_method="GET")
        assert step.type == "function"
        assert step.function_headers == {}
        assert step.function_body is None

    def test_branch_step(self):
        from cx_task_harness.models.steps import BranchStep

        step = BranchStep(
            id="check", name="Check Status",
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

        step = BrowserStep(id="automate", name="Browser Action", url="https://admin.example.com", actions=[{"action": "click", "selector": "#btn"}])
        assert step.type == "browser"


class TestStepDiscriminatedUnion:
    def test_parse_agent_step(self):
        from pydantic import TypeAdapter
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        data = {"id": "s1", "name": "Agent", "type": "agent", "instructions": {"role": "Agent", "conversation_flow": ["Step 1"], "exit_conditions": ["Done"]}}
        step = adapter.validate_python(data)
        assert step.type == "agent"
        assert step.__class__.__name__ == "AgentStep"

    def test_parse_message_step(self):
        from pydantic import TypeAdapter
        from cx_task_harness.models.steps import Step

        adapter = TypeAdapter(Step)
        data = {"id": "s1", "name": "Msg", "type": "message", "message_content": "Hi"}
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
        json_str = json.dumps({"id": "s1", "name": "Code", "type": "code", "code": "return 1;"})
        step = adapter.validate_json(json_str)
        assert step.type == "code"


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

        item = SetupItem(node_id="func_1", node_name="Order API", type="credential", description="API key needed", fields=["api_key", "base_url"])
        assert item.node_id == "func_1"
        assert len(item.fields) == 2

    def test_template_summary(self):
        from cx_task_harness.models.n8n import TemplateSummary

        ts = TemplateSummary(id="ecommerce/order-cancel", name="Order Cancellation", description="Handle order cancellations", industry="ecommerce", locale="en", steps_count=9, step_types=["agent", "function", "branch", "action"])
        assert ts.id == "ecommerce/order-cancel"
