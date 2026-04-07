"""Tests for validate_n8n tool."""

import json


def _make_valid_workflow():
    """Create a minimal valid n8n workflow for testing."""
    return {
        "name": "Test Workflow",
        "nodes": [
            {
                "id": "trigger",
                "name": "Manual Trigger",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {},
            }
        ],
        "connections": {},
        "active": False,
        "settings": {},
        "tags": [],
        "meta": {},
    }


class TestValidateN8n:
    def test_valid_workflow(self):
        from cx_task_harness.tools.n8n_validator import validate_n8n
        wf = _make_valid_workflow()
        result = validate_n8n(json.dumps(wf))
        assert result["valid"] is True
        assert result["errors"] == []

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

    def test_returns_n8n_version(self):
        from cx_task_harness.tools.n8n_validator import validate_n8n
        wf = _make_valid_workflow()
        result = validate_n8n(json.dumps(wf))
        assert "n8n_version" in result
        assert result["n8n_version"] == "1.x"
