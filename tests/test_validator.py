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
            "id": "t", "name": "T", "description": "T",
            "trigger": {"intent": "test"},
            "steps": [{"id": "b1", "name": "Branch", "type": "branch", "branches": [{"condition": "yes", "next_step": "ghost"}]}],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("ghost" in e for e in result["errors"])

    def test_circular_reference(self):
        from cx_task_harness.tools.validator import validate_task_spec
        spec = {
            "id": "t", "name": "T", "description": "T",
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
            "id": "t", "name": "T", "description": "T",
            "trigger": {"intent": ""},
            "steps": [{"id": "s", "name": "S", "type": "message", "message_content": "Hi"}],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("intent" in e.lower() for e in result["errors"])

    def test_duplicate_memory_keys(self):
        from cx_task_harness.tools.validator import validate_task_spec
        spec = {
            "id": "t", "name": "T", "description": "T",
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
            "id": "t", "name": "T", "description": "T",
            "trigger": {"intent": "test"},
            "steps": [{
                "id": "a", "name": "Agent", "type": "agent",
                "instructions": {"role": "Agent", "conversation_flow": ["Step"], "exit_conditions": []},
            }],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is False
        assert any("exit_conditions" in e for e in result["errors"])


class TestValidatorWarnings:
    def test_unreachable_step(self):
        from cx_task_harness.tools.validator import validate_task_spec
        spec = {
            "id": "t", "name": "T", "description": "T",
            "trigger": {"intent": "test"},
            "steps": [
                {"id": "reachable", "name": "R", "type": "message", "message_content": "Hi"},
                {"id": "orphan", "name": "O", "type": "message", "message_content": "Alone"},
            ],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is True
        assert any("orphan" in w.lower() for w in result["warnings"])

    def test_function_without_on_failure(self):
        from cx_task_harness.tools.validator import validate_task_spec
        spec = {
            "id": "t", "name": "T", "description": "T",
            "trigger": {"intent": "test"},
            "steps": [{"id": "f", "name": "API", "type": "function", "function_url": "https://example.com"}],
        }
        result = validate_task_spec(json.dumps(spec))
        assert result["valid"] is True
        assert any("on_failure" in w for w in result["warnings"])
