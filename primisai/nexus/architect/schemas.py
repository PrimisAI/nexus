from pydantic import BaseModel
from typing import List, Optional

# Tool Schema
class ParameterProperty(BaseModel):
    argument: str
    type: str
    description: str

class ToolParameters(BaseModel):
    type: str
    properties: List[ParameterProperty]
    required: List[str]

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
    validation_constraints: List[str]

# Agent Schema
class AgentDefinition(BaseModel):
    name: str
    system_message: str
    use_tools: bool
    keep_history: bool
    tools: List[Tool]
    output_schema: Optional[str] = None
    strict: bool = False
    validation_constraints: List[str]

# Supervisor Schema
class SupervisorDefinition(BaseModel):
    name: str
    is_assistant: bool
    system_message: str
    managed_agents: List[str]
    managed_assistant_supervisors: List[str]
    validation_constraints: List[str]

# Complete Workflow Schema
class WorkflowDefinition(BaseModel):
    main_supervisor: SupervisorDefinition
    assistant_supervisors: List[SupervisorDefinition]
    agents: List[AgentDefinition]