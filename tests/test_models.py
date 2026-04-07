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
