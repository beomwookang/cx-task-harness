"""Map TaskSpec steps to n8n nodes."""

from __future__ import annotations

from cx_task_harness.models.n8n import SetupItem
from cx_task_harness.models.steps import (
    ActionStep, AgentStep, BranchStep, BrowserStep,
    CodeStep, FunctionStep, MessageStep,
)
from cx_task_harness.models.task_spec import TaskSpec
from cx_task_harness.n8n.node_templates import (
    make_ai_agent_node, make_code_node, make_http_request_node,
    make_if_node, make_manual_trigger, make_mock_response_node, make_set_node,
    make_switch_node,
)


def map_task_spec(spec: TaskSpec, include_mock_data: bool = True) -> dict:
    """Convert a TaskSpec to n8n nodes, connections, and setup requirements."""
    nodes: list[dict] = []
    connections: dict[str, list[str]] = {}
    setup_required: list[dict] = []

    trigger = make_manual_trigger(node_id="trigger")
    nodes.append(trigger)

    if spec.memory:
        assignments = {m.key: "" for m in spec.memory}
        mem_node = make_set_node("init_memory", "Initialize Memory", assignments)
        nodes.append(mem_node)
        connections["trigger"] = ["init_memory"]
        first_connection_source = "init_memory"
    else:
        first_connection_source = "trigger"

    step_node_ids: dict[str, str] = {}

    for step in spec.steps:
        node_id = f"step_{step.id}"
        step_node_ids[step.id] = node_id

        if isinstance(step, AgentStep):
            system_msg = _build_agent_system_message(step)
            node = make_ai_agent_node(node_id, step.name, system_msg)
            nodes.append(node)

        elif isinstance(step, CodeStep):
            node = make_code_node(node_id, step.name, step.code, step.language)
            nodes.append(node)

        elif isinstance(step, MessageStep):
            node = make_set_node(node_id, step.name, {"response": step.message_content})
            nodes.append(node)

        elif isinstance(step, ActionStep):
            node = make_set_node(
                node_id, step.name,
                {"action": step.action_type, **{str(k): str(v) for k, v in step.action_params.items()}},
            )
            nodes.append(node)

        elif isinstance(step, FunctionStep):
            node = make_http_request_node(
                node_id, step.name, url=step.function_url,
                method=step.function_method,
                headers=step.function_headers or None,
                body=step.function_body,
            )
            nodes.append(node)
            setup_required.append(
                SetupItem(
                    node_id=node_id, node_name=step.name, type="credential",
                    description=f"Configure {step.function_method} {step.function_url}",
                    fields=["url", "authentication"],
                ).model_dump()
            )
            if include_mock_data:
                mock_id = f"mock_{step.id}"
                mock_node = make_mock_response_node(mock_id, step.name, {"status": "ok", "mock": True})
                nodes.append(mock_node)
                step_node_ids[f"_mock_{step.id}"] = mock_id

        elif isinstance(step, BranchStep):
            conditions = []
            for branch in step.branches:
                conditions.append({
                    "variable": branch.variable or "value",
                    "operator": branch.operator or "eq",
                    "value": branch.value or "",
                })
            node = make_switch_node(node_id, step.name, conditions)
            nodes.append(node)

        elif isinstance(step, BrowserStep):
            node = make_http_request_node(node_id, f"[Browser] {step.name}", url=step.url, method="GET")
            nodes.append(node)
            setup_required.append(
                SetupItem(
                    node_id=node_id, node_name=step.name, type="config",
                    description="Browser automation step — requires manual n8n configuration",
                    fields=["url", "actions"],
                ).model_dump()
            )

    if spec.steps:
        first_step_node = step_node_ids[spec.steps[0].id]
        connections.setdefault(first_connection_source, []).append(first_step_node)

    branch_node_ids: set[str] = set()

    for step in spec.steps:
        src = step_node_ids[step.id]
        if isinstance(step, BranchStep):
            branch_node_ids.add(src)
            for branch in step.branches:
                if branch.next_step in step_node_ids:
                    connections.setdefault(src, []).append(step_node_ids[branch.next_step])
            if step.default_branch and step.default_branch in step_node_ids:
                connections.setdefault(src, []).append(step_node_ids[step.default_branch])
        else:
            if step.next_step and step.next_step in step_node_ids:
                connections.setdefault(src, []).append(step_node_ids[step.next_step])
            if step.on_failure and step.on_failure in step_node_ids:
                connections.setdefault(src, []).append(step_node_ids[step.on_failure])

    return {
        "nodes": nodes,
        "connections": connections,
        "setup_required": setup_required,
        "branch_node_ids": branch_node_ids,
    }


def _build_agent_system_message(step: AgentStep) -> str:
    inst = step.instructions
    parts = [f"Role: {inst.role}", "", "Conversation Flow:"]
    for i, flow in enumerate(inst.conversation_flow, 1):
        parts.append(f"{i}. {flow}")
    parts.extend(["", "Exit Conditions:"])
    for cond in inst.exit_conditions:
        parts.append(f"- {cond}")
    if inst.exceptions:
        parts.extend(["", "Exceptions:"])
        for exc in inst.exceptions:
            parts.append(f"- {exc}")
    return "\n".join(parts)
