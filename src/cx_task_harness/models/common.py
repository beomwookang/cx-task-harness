"""Common model types used across CX Task Spec."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentInstruction(BaseModel):
    """Structured instruction for an LLM-driven conversational step."""

    role: str = Field(description="Role definition for the agent")
    conversation_flow: list[str] = Field(description="Ordered conversation steps")
    exit_conditions: list[str] = Field(description="Conditions that end this step")
    exceptions: list[str] = Field(
        default_factory=list, description="Edge cases and exception handling"
    )


class BranchCondition(BaseModel):
    """Routing condition for a branch step."""

    condition: str = Field(description="Human-readable condition description")
    variable: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    next_step: str = Field(description="Target step ID")


class MemoryVariable(BaseModel):
    """Temporary variable scoped to a single task execution."""

    key: str = Field(description="Variable name (e.g., 'order_id')")
    type: Literal["string", "number", "boolean", "object", "array"]
    description: str


class TriggerFilter(BaseModel):
    """Condition filter for trigger activation."""

    field: str = Field(description="Filter target (e.g., 'customer.tier')")
    operator: Literal["eq", "neq", "contains", "gt", "lt", "in"]
    value: str | list[str]


class Trigger(BaseModel):
    """Task activation condition."""

    intent: str = Field(description="Trigger intent in natural language")
    keywords: list[str] = Field(default_factory=list)
    filters: list[TriggerFilter] = Field(default_factory=list)


class AutomationPotential(BaseModel):
    """Automation feasibility assessment."""

    score: float = Field(ge=0, le=1)
    reasoning: str
    estimated_resolution_rate: Optional[float] = Field(None, ge=0, le=1)
