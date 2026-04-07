"""Step type models with Pydantic Discriminated Union."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Discriminator, Field

from cx_task_harness.models.common import AgentInstruction, BranchCondition


class StepBase(BaseModel):
    """Common fields for all step types."""

    id: str
    name: str
    next_step: Optional[str] = None
    on_failure: Optional[str] = None


class AgentStep(StepBase):
    type: Literal["agent"] = "agent"
    instructions: AgentInstruction


class CodeStep(StepBase):
    type: Literal["code"] = "code"
    code: str
    language: Literal["javascript", "python"] = "javascript"


class MessageStep(StepBase):
    type: Literal["message"] = "message"
    message_content: str


class ActionStep(StepBase):
    type: Literal["action"] = "action"
    action_type: str
    action_params: dict = Field(default_factory=dict)


class FunctionStep(StepBase):
    type: Literal["function"] = "function"
    function_url: str
    function_method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    function_headers: dict = Field(default_factory=dict)
    function_body: Optional[dict] = None


class BranchStep(StepBase):
    type: Literal["branch"] = "branch"
    branches: list[BranchCondition]
    default_branch: Optional[str] = None
    next_step: None = None


class BrowserStep(StepBase):
    type: Literal["browser"] = "browser"
    url: str
    actions: list[dict]


Step = Annotated[
    AgentStep | CodeStep | MessageStep | ActionStep | FunctionStep | BranchStep | BrowserStep,
    Discriminator("type"),
]
