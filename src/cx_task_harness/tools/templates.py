"""list_templates tool implementation."""

from __future__ import annotations

import json as json_module
from pathlib import Path

from cx_task_harness.models.task_spec import TaskSpec

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def list_templates(
    industry: str | None = None,
    locale: str = "en",
) -> dict:
    """List available industry templates."""
    templates: list[dict] = []

    for json_file in sorted(_TEMPLATES_DIR.rglob("*.json")):
        try:
            data = json_module.loads(json_file.read_text())
            spec = TaskSpec(**data)
        except Exception:
            continue

        file_industry = json_file.parent.name

        if industry and file_industry != industry:
            continue
        if spec.locale != locale:
            continue

        template_id = f"{file_industry}/{json_file.stem.rsplit('.', 1)[0]}"
        step_types = list({s.type for s in spec.steps})

        templates.append({
            "id": template_id,
            "name": spec.name,
            "description": spec.description,
            "industry": file_industry,
            "locale": spec.locale,
            "steps_count": len(spec.steps),
            "step_types": sorted(step_types),
        })

    return {"templates": templates}


def get_template(template_id: str, locale: str = "en") -> str | None:
    """Load a template's full TaskSpec JSON by ID and locale."""
    parts = template_id.split("/")
    if len(parts) != 2:
        return None

    file_path = _TEMPLATES_DIR / parts[0] / f"{parts[1]}.{locale}.json"
    if file_path.exists():
        return file_path.read_text()
    return None
