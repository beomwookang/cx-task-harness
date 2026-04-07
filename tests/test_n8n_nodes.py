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
        node = make_set_node(node_id="set_1", name="Init Memory", assignments={"order_id": "", "cancel_reason": ""})
        assert node["type"] == "n8n-nodes-base.set"
        assert node["name"] == "Init Memory"

    def test_code_node(self):
        from cx_task_harness.n8n.node_templates import make_code_node
        node = make_code_node(node_id="code_1", name="Validate", code="return items;", language="javascript")
        assert node["type"] == "n8n-nodes-base.code"
        assert node["parameters"]["jsCode"] == "return items;"

    def test_code_node_python(self):
        from cx_task_harness.n8n.node_templates import make_code_node
        node = make_code_node(node_id="code_1", name="Process", code="return items", language="python")
        assert node["parameters"]["language"] == "python"
        assert node["parameters"]["pythonCode"] == "return items"

    def test_http_request_node(self):
        from cx_task_harness.n8n.node_templates import make_http_request_node
        node = make_http_request_node(node_id="http_1", name="Call API", url="https://api.example.com", method="GET", headers={"Authorization": "Bearer key"})
        assert node["type"] == "n8n-nodes-base.httpRequest"
        assert node["parameters"]["url"] == "https://api.example.com"
        assert node["parameters"]["method"] == "GET"

    def test_if_node(self):
        from cx_task_harness.n8n.node_templates import make_if_node
        node = make_if_node(node_id="if_1", name="Check Status", conditions=[{"variable": "status", "operator": "eq", "value": "active"}])
        assert node["type"] == "n8n-nodes-base.if"

    def test_ai_agent_node(self):
        from cx_task_harness.n8n.node_templates import make_ai_agent_node
        node = make_ai_agent_node(node_id="agent_1", name="Support Agent", system_message="You are a helpful support agent.")
        assert node["type"] == "@n8n/n8n-nodes-langchain.agent"

    def test_all_nodes_have_required_fields(self):
        from cx_task_harness.n8n.node_templates import make_manual_trigger, make_set_node, make_code_node
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
