"""CX Task Harness — FastMCP server."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from cx_task_harness.tools.converter import convert_to_n8n as _convert_to_n8n
from cx_task_harness.tools.n8n_validator import validate_n8n as _validate_n8n
from cx_task_harness.tools.templates import get_template, list_templates as _list_templates
from cx_task_harness.tools.validator import validate_task_spec as _validate_task_spec

mcp = FastMCP(
    "cx-task-harness",
    instructions="Validates CX Task Specs and converts them to n8n workflows",
)


@mcp.tool()
def validate_task_spec(task_spec: str) -> str:
    """Validate a CX Task Spec JSON for structural integrity.

    Checks: Pydantic schema, step references, circular dependencies,
    branch targets, agent exit conditions, memory key uniqueness.

    Args:
        task_spec: Complete TaskSpec as a JSON string.
    """
    result = _validate_task_spec(task_spec)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def convert_to_n8n(
    task_spec: str,
    include_mock_data: bool = True,
    target_n8n_version: str = "1.x",
) -> str:
    """Convert a CX Task Spec to an importable n8n workflow JSON.

    Args:
        task_spec: Validated TaskSpec as a JSON string.
        include_mock_data: Insert mock response nodes for API steps (default: true).
        target_n8n_version: Target n8n version for compatibility (default: "1.x").
    """
    result = _convert_to_n8n(task_spec, include_mock_data, target_n8n_version)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def validate_n8n(workflow: str) -> str:
    """Validate an n8n workflow JSON against the n8n schema.

    Args:
        workflow: n8n workflow as a JSON string.
    """
    result = _validate_n8n(workflow)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def list_templates(
    industry: str | None = None,
    locale: str = "en",
) -> str:
    """List available industry task spec templates.

    Args:
        industry: Filter by industry (e.g., "ecommerce", "travel"). Omit for all.
        locale: Language locale — "en" or "ko" (default: "en").
    """
    result = _list_templates(industry=industry, locale=locale)
    return json.dumps(result, ensure_ascii=False)


@mcp.resource("template://{template_id}/{locale}")
def read_template(template_id: str, locale: str = "en") -> str:
    """Read a full TaskSpec template by ID and locale."""
    content = get_template(template_id, locale)
    if content is None:
        return json.dumps({"error": f"Template '{template_id}' ({locale}) not found"})
    return content
