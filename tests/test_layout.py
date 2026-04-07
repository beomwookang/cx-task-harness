"""Tests for n8n node layout algorithm."""


class TestLayout:
    def test_linear_layout(self):
        from cx_task_harness.n8n.layout import compute_layout

        nodes = [
            {"id": "a", "position": [0, 0]},
            {"id": "b", "position": [0, 0]},
            {"id": "c", "position": [0, 0]},
        ]
        connections = {"a": ["b"], "b": ["c"]}
        compute_layout(nodes, connections, start_id="a")

        node_map = {n["id"]: n for n in nodes}
        assert node_map["a"]["position"][1] < node_map["b"]["position"][1]
        assert node_map["b"]["position"][1] < node_map["c"]["position"][1]
        assert node_map["a"]["position"][0] == node_map["b"]["position"][0]

    def test_branch_layout(self):
        from cx_task_harness.n8n.layout import compute_layout

        nodes = [
            {"id": "a", "position": [0, 0]},
            {"id": "b", "position": [0, 0]},
            {"id": "c", "position": [0, 0]},
        ]
        connections = {"a": ["b", "c"]}
        compute_layout(nodes, connections, start_id="a")

        node_map = {n["id"]: n for n in nodes}
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
