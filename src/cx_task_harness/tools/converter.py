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
    """Convert a TaskSpec JSON string to an n8n workflow."""
    try:
        data = json_module.loads(task_spec)
    except json_module.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    try:
        spec = TaskSpec(**data)
    except ValidationError as e:
        return {"error": f"Invalid TaskSpec: {e}"}

    map_result = map_task_spec(spec, include_mock_data=include_mock_data)

    compute_layout(map_result["nodes"], map_result["connections"], start_id="trigger")

    n8n_connections = _build_n8n_connections(
        map_result["nodes"], map_result["connections"], map_result.get("branch_node_ids"),
    )

    workflow = {
        "name": spec.name,
        "nodes": map_result["nodes"],
        "connections": n8n_connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": [],
        "meta": {
            "generatedBy": "cx-task-harness",
            "taskSpecId": spec.id,
            "targetN8nVersion": target_n8n_version,
        },
    }

    return {"workflow": workflow, "setup_required": map_result["setup_required"]}


def _build_n8n_connections(
    nodes: list[dict],
    connections: dict[str, list[str]],
    branch_node_ids: set[str] | None = None,
) -> dict:
    branch_node_ids = branch_node_ids or set()
    node_name_by_id = {n["id"]: n["name"] for n in nodes}
    n8n_conns: dict = {}

    for src_id, target_ids in connections.items():
        src_name = node_name_by_id.get(src_id, src_id)

        if src_id in branch_node_ids:
            # Each target gets its own output index (Switch node)
            outputs: list[list[dict]] = []
            for target_id in target_ids:
                target_name = node_name_by_id.get(target_id, target_id)
                outputs.append([{"node": target_name, "type": "main", "index": 0}])
        else:
            # All targets share output index 0
            output_0: list[dict] = []
            for target_id in target_ids:
                target_name = node_name_by_id.get(target_id, target_id)
                output_0.append({"node": target_name, "type": "main", "index": 0})
            outputs = [output_0] if output_0 else []

        if outputs:
            n8n_conns[src_name] = {"main": outputs}

    return n8n_conns
