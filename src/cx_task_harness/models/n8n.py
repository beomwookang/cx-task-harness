"""Models for n8n conversion and validation results."""

from __future__ import annotations

from pydantic import BaseModel


class SetupItem(BaseModel):
    """An item that requires manual setup in the n8n workflow."""

    node_id: str
    node_name: str
    type: str
    description: str
    fields: list[str]


class TemplateSummary(BaseModel):
    """Summary of an industry template."""

    id: str
    name: str
    description: str
    industry: str
    locale: str
    steps_count: int
    step_types: list[str]
