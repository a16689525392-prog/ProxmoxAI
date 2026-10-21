from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class Action(str, Enum):
    start = "start"
    shutdown = "shutdown"
    snapshot = "snapshot"

class VM(BaseModel):
    vmid: int
    node: str
    name: str
    status: str
    cpu: float = 0
    mem: int = 0
    maxmem: int = 0

class AgentRequest(BaseModel):
    text: str = Field(min_length=2, max_length=500)

class Plan(BaseModel):
    intent: Literal["list", "status", "start", "shutdown", "snapshot"]
    vmid: int | None = None
    snapname: str | None = None
    explanation: str = ""
    source: Literal["rules", "llm"] = "rules"

class PreviewRequest(BaseModel):
    action: Action
    snapname: str | None = Field(default=None, max_length=40, pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")

class ExecuteRequest(BaseModel):
    approval_id: str = Field(min_length=20, max_length=200)
