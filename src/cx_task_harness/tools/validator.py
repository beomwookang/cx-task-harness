"""validate_task_spec tool implementation."""

from __future__ import annotations

import json as json_module

from pydantic import ValidationError

from cx_task_harness.models.steps import AgentStep, BranchStep, CodeStep, FunctionStep
from cx_task_harness.models.task_spec import TaskSpec


def validate_task_spec(task_spec: str) -> dict:
    """Validate a CX Task Spec JSON string.

    Returns {"valid": bool, "errors": list[str], "warnings": list[str]}.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Parse JSON + Pydantic validation
    try:
        data = json_module.loads(task_spec)
    except json_module.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": []}

    try:
        spec = TaskSpec(**data)
    except ValidationError as e:
        return {
            "valid": False,
            "errors": [f"Schema validation error: {err['msg']}" for err in e.errors()],
            "warnings": [],
        }

    step_ids = {step.id for step in spec.steps}

    # 2. Empty trigger intent
    if not spec.trigger.intent.strip():
        errors.append("Trigger intent must not be empty")

    # 3. Duplicate memory keys
    mem_keys = [m.key for m in spec.memory]
    seen_keys: set[str] = set()
    for key in mem_keys:
        if key in seen_keys:
            errors.append(f"Duplicate memory variable key: '{key}'")
        seen_keys.add(key)

    # 4. Validate step references
    for step in spec.steps:
        if step.next_step is not None and step.next_step not in step_ids:
            errors.append(
                f"Step '{step.id}' references non-existent next_step '{step.next_step}'"
            )
        if step.on_failure is not None and step.on_failure not in step_ids:
            errors.append(
                f"Step '{step.id}' references non-existent on_failure '{step.on_failure}'"
            )
        if isinstance(step, BranchStep):
            for branch in step.branches:
                if branch.next_step not in step_ids:
                    errors.append(
                        f"Branch step '{step.id}' references non-existent target '{branch.next_step}'"
                    )
            if step.default_branch is not None and step.default_branch not in step_ids:
                errors.append(
                    f"Branch step '{step.id}' references non-existent default_branch '{step.default_branch}'"
                )
        if isinstance(step, AgentStep):
            if not step.instructions.exit_conditions:
                errors.append(
                    f"Agent step '{step.id}' must have at least one exit_conditions entry"
                )

    # 5. Circular reference detection
    if not errors:
        _check_circular(spec, errors)

    # 6. Warnings: unreachable steps
    reachable = _find_reachable_steps(spec)
    for step in spec.steps:
        if step.id not in reachable and step != spec.steps[0]:
            warnings.append(f"Step '{step.id}' is unreachable (no path leads to it)")

    # 7. Warnings: FunctionStep/CodeStep without on_failure
    for step in spec.steps:
        if isinstance(step, (FunctionStep, CodeStep)) and step.on_failure is None:
            warnings.append(f"Step '{step.id}' ({step.type}) has no on_failure handler")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _check_circular(spec: TaskSpec, errors: list[str]) -> None:
    adjacency: dict[str, list[str]] = {}
    for step in spec.steps:
        targets: list[str] = []
        if step.next_step is not None:
            targets.append(step.next_step)
        if step.on_failure is not None:
            targets.append(step.on_failure)
        if isinstance(step, BranchStep):
            for branch in step.branches:
                targets.append(branch.next_step)
            if step.default_branch is not None:
                targets.append(step.default_branch)
        adjacency[step.id] = targets

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {sid: WHITE for sid in adjacency}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in adjacency.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                errors.append(f"Circular reference detected involving step '{neighbor}'")
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    for node in adjacency:
        if color[node] == WHITE:
            dfs(node)


def _find_reachable_steps(spec: TaskSpec) -> set[str]:
    if not spec.steps:
        return set()
    reachable: set[str] = set()
    queue = [spec.steps[0].id]
    step_map = {step.id: step for step in spec.steps}
    while queue:
        current_id = queue.pop(0)
        if current_id in reachable or current_id not in step_map:
            continue
        reachable.add(current_id)
        step = step_map[current_id]
        if step.next_step is not None:
            queue.append(step.next_step)
        if step.on_failure is not None:
            queue.append(step.on_failure)
        if isinstance(step, BranchStep):
            for branch in step.branches:
                queue.append(branch.next_step)
            if step.default_branch is not None:
                queue.append(step.default_branch)
    return reachable
