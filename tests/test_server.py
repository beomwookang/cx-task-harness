"""Integration tests for MCP server."""

import json
import pytest


class TestServerTools:
    def test_validate_task_spec_tool(self, minimal_task_spec_dict):
        from cx_task_harness.server import validate_task_spec
        result_str = validate_task_spec(json.dumps(minimal_task_spec_dict))
        data = json.loads(result_str)
        assert data["valid"] is True

    def test_convert_to_n8n_tool(self, minimal_task_spec_dict):
        from cx_task_harness.server import convert_to_n8n
        result_str = convert_to_n8n(json.dumps(minimal_task_spec_dict))
        data = json.loads(result_str)
        assert "workflow" in data

    def test_validate_n8n_tool(self, minimal_task_spec_dict):
        from cx_task_harness.server import convert_to_n8n, validate_n8n
        convert_result = json.loads(convert_to_n8n(json.dumps(minimal_task_spec_dict)))
        result_str = validate_n8n(json.dumps(convert_result["workflow"]))
        data = json.loads(result_str)
        assert data["valid"] is True

    def test_list_templates_tool(self):
        from cx_task_harness.server import list_templates
        result_str = list_templates(locale="en")
        data = json.loads(result_str)
        assert "templates" in data
        assert len(data["templates"]) >= 1

    def test_validate_invalid_spec(self):
        from cx_task_harness.server import validate_task_spec
        result_str = validate_task_spec("not json")
        data = json.loads(result_str)
        assert data["valid"] is False

    def test_full_pipeline(self, order_cancel_task_spec_dict):
        from cx_task_harness.server import validate_task_spec, convert_to_n8n, validate_n8n
        spec_json = json.dumps(order_cancel_task_spec_dict)

        v = json.loads(validate_task_spec(spec_json))
        assert v["valid"]

        c = json.loads(convert_to_n8n(spec_json))
        assert "workflow" in c

        n = json.loads(validate_n8n(json.dumps(c["workflow"])))
        assert n["valid"]
