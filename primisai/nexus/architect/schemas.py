from pydantic import BaseModel,Field
from typing import List, Optional

# Tool Schema
class ParameterProperty(BaseModel):
    argument: str
    type: str
    description: str

class ToolParameters(BaseModel):
    type: str
    properties: list[ParameterProperty]
    required: list[str]

class ToolFunctionDef(BaseModel):
    name: str
    description: str
    parameters: ToolParameters

class ToolMetadata(BaseModel):
    type: str
    function: ToolFunctionDef

class Tool(BaseModel):
    metadata: ToolMetadata 
    implementation: str
    validation_constraints: list[str]

# Agent Schema
class AgentDefinition(BaseModel):
    name: str
    system_message: str
    use_tools: bool
    keep_history: bool
    tools: list[Tool] = Field(default_factory=list) 
    output_schema: str | None = None
    strict: bool = False
    validation_constraints: list[str]

# Supervisor Schema
class SupervisorDefinition(BaseModel):
    name: str
    is_assistant: bool
    system_message: str
    managed_assistant_supervisors: list[str]
    managed_agents: list[str] = Field(default_factory=list) 
    validation_constraints: list[str]

# Complete Workflow Schema
class WorkflowDefinition(BaseModel):
    main_supervisor: SupervisorDefinition
    assistant_supervisors: list[SupervisorDefinition]
    agents: list[AgentDefinition]