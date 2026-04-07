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
        assert "connections" in wf
        assert isinstance(wf["connections"], dict)

    def test_include_mock_data_flag(self, order_cancel_task_spec_dict):
        from cx_task_harness.tools.converter import convert_to_n8n
        result_with_mock = convert_to_n8n(json.dumps(order_cancel_task_spec_dict), include_mock_data=True)
        result_no_mock = convert_to_n8n(json.dumps(order_cancel_task_spec_dict), include_mock_data=False)
        assert len(result_with_mock["workflow"]["nodes"]) > len(result_no_mock["workflow"]["nodes"])
