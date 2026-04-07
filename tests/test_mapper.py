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
        assert len(result["nodes"]) >= 2

    def test_map_order_cancel(self, order_cancel_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec
        spec = TaskSpec(**order_cancel_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=False)
        assert any("n8n-nodes-base.httpRequest" in n["type"] for n in result["nodes"])
        assert any("n8n-nodes-base.switch" in n["type"] for n in result["nodes"])
        assert len(result["setup_required"]) > 0

    def test_mock_data_insertion(self, order_cancel_task_spec_dict):
        from cx_task_harness.n8n.mapper import map_task_spec
        spec = TaskSpec(**order_cancel_task_spec_dict)
        result = map_task_spec(spec, include_mock_data=True)
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
