"""Top-level TaskSpec model."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from cx_task_harness.models.common import (
    AutomationPotential,
    MemoryVariable,
    Trigger,
)
from cx_task_harness.models.steps import Step


class TaskSpec(BaseModel):
    """CX Task Spec — platform-agnostic schema for CX automation tasks."""

    id: str
    name: str
    description: str
    industry: Optional[str] = None
    locale: Literal["ko", "en"] = "en"

    trigger: Trigger
    memory: list[MemoryVariable] = Field(default_factory=list)
    steps: list[Step]

    automation_potential: Optional[AutomationPotential] = None
    metadata: dict = Field(default_factory=dict)
