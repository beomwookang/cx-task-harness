"""validate_n8n tool implementation."""

from __future__ import annotations

import json as json_module
from pathlib import Path

import jsonschema


_SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "schemas" / "n8n_workflow.schema.json"
_BUNDLED_SCHEMA_PATH = Path(__file__).parent.parent / "_schemas" / "n8n_workflow.schema.json"

_N8N_TARGET_VERSION = "1.x"


def _load_schema() -> dict:
    """Load n8n workflow JSON Schema."""
    for path in [_BUNDLED_SCHEMA_PATH, _SCHEMA_PATH]:
        if path.exists():
            return json_module.loads(path.read_text())
    raise FileNotFoundError("n8n workflow schema not found")


def validate_n8n(workflow: str) -> dict:
    """Validate an n8n workflow JSON string against the schema.

    Returns {"valid": bool, "errors": list[str], "n8n_version": str}.
    """
    try:
        data = json_module.loads(workflow)
    except json_module.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "n8n_version": _N8N_TARGET_VERSION}

    try:
        schema = _load_schema()
    except FileNotFoundError:
        return {
            "valid": False,
            "errors": ["n8n workflow schema file not found"],
            "n8n_version": _N8N_TARGET_VERSION,
        }

    errors: list[str] = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(data):
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"{path}: {error.message}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "n8n_version": _N8N_TARGET_VERSION,
    }
