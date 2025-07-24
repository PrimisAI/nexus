from primisai.nexus.core import Agent, Supervisor
from typing import Dict, Any
from primisai.nexus.architect.schemas import Tool, AgentDefinition, SupervisorDefinition, WorkflowDefinition


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ToolBuilder:
    """
    Translates a structured workflow definition into executable Python code.

    This class acts as the "code generator" or "compiler" in the Archtect
    pipeline. It takes a formal, structured definition of a workflow (as
    produced by the `WorkflowStructurer`) and dynamically generates a runnable
    Python script.

    The generated script orchestrates the execution of the various components
    (nodes) in the correct order, handling the data flow between them as
e   defined by the edges of the workflow graph. The final output is a
    self-contained piece of code ready to be executed or passed to the
    `Evaluator` for performance assessment.
    """

    def __init__(self, tool_definition: Tool):
        """
        Initializes the ToolBuilder with a complete workflow definition.

        Args:
            tool_definition (Tool): A structured object containing the full
                specification of the workflow to be built. This object includes
                the name, description, a list of component `nodes`, and a list
                of `edges` that define the data flow graph.
        """
        self.definition = tool_definition

    def build(self) -> Dict[str, Any]:
        """Convert Tool definition to Nexus tool format"""
        try:
            # Create the tool function from implementation string
            namespace = {}
            exec(self.definition.implementation, namespace)
            tool_func = namespace[self.definition.metadata.function.name]

            # Construct the metadata in the correct format
            metadata = {
                "type": self.definition.metadata.type,
                "function": {
                    "name": self.definition.metadata.function.name,
                    "description": self.definition.metadata.function.description,
                    "parameters": {
                        "type": self.definition.metadata.function.parameters.type,
                        "properties": {
                            prop.argument: {
                                "type": prop.type,
                                "description": prop.description
                            } for prop in self.definition.metadata.function.parameters.properties
                        },
                        "required": self.definition.metadata.function.parameters.required
                    }
                }
            }

            return {"tool": tool_func, "metadata": metadata}

        except Exception as e:
            print(f"Error in tool building: {str(e)}")
            raise

    def validate(self) -> bool:
        """Run validation tests based on constraints"""
        try:
            # Validate function implementation
            namespace = {}
            exec(self.definition.implementation, namespace)
            tool_func = namespace[self.definition.metadata.function.name]

            # Validate function signature matches parameters
            import inspect
            sig = inspect.signature(tool_func)
            param_names = set(sig.parameters.keys())
            required_params = set(p.argument for p in self.definition.metadata.function.parameters.properties)

            if param_names != required_params:
                print(f"Parameter mismatch: function has {param_names}, metadata requires {required_params}")
                return False

            return True

        except Exception as e:
            print(f"Tool validation failed: {str(e)}")
            return False


class AgentBuilder:

    def __init__(self, agent_definition: AgentDefinition, llm_config: Dict[str, str]):
        self.definition = agent_definition
        self.llm_config = llm_config

    def validate(self) -> bool:
        """
        Validate agent definition meets all requirements.
        
        Validates:
        1. Basic requirements (name, system message)
        2. Tool configuration
        3. History management settings
        4. Output schema configuration  # New validation
        """
        try:
            # 1. Basic validation
            self._validate_basic_requirements()

            # 2. Tool validation
            self._validate_tool_configuration()

            # 3. History management validation
            self._validate_history_management()

            # 4. Output schema validation  # New method
            self._validate_output_schema()

            return True
        except ValidationError as e:
            print(f"Agent validation failed: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error in agent validation: {str(e)}")
            return False

    def _validate_basic_requirements(self):
        """Validate basic agent requirements"""
        if not self.definition.name or not self.definition.name.strip():
            raise ValidationError("Agent name cannot be empty")

        if not self.definition.system_message or not self.definition.system_message.strip():
            raise ValidationError("System message cannot be empty")

    def _validate_tool_configuration(self):
        """Validate tool configuration consistency"""
        if self.definition.use_tools and not self.definition.tools:
            raise ValidationError("Agent is configured to use tools but no tools provided")

        if not self.definition.use_tools and self.definition.tools:
            raise ValidationError("Tools provided but agent not configured to use them")

        # Validate each tool
        if self.definition.tools:
            tool_names = set()
            for tool in self.definition.tools:
                # Check for duplicate tool names
                tool_name = tool.metadata.function.name
                if tool_name in tool_names:
                    raise ValidationError(f"Duplicate tool name found: {tool_name}")
                tool_names.add(tool_name)

    def _validate_history_management(self):
        """Validate history management settings"""
        if self.definition.keep_history is None:
            raise ValidationError("History management setting must be specified")

    def _validate_output_schema(self):
        """Validate output schema configuration if provided"""
        if self.definition.output_schema:
            try:
                # Try to parse the schema string as JSON
                import json
                schema = json.loads(self.definition.output_schema)

                # Basic schema validation
                if not isinstance(schema, dict):
                    raise ValidationError("Output schema must be a valid JSON object")

                if "type" not in schema:
                    raise ValidationError("Output schema must have 'type' field")

                if schema["type"] != "object":
                    raise ValidationError("Output schema type must be 'object'")

                if "properties" not in schema:
                    raise ValidationError("Output schema must have 'properties' field")

            except json.JSONDecodeError:
                raise ValidationError("Output schema must be valid JSON")

    def build(self) -> Agent:
        """Build agent if validation passes"""
        if not self.validate():
            raise ValidationError(f"Validation failed for agent {self.definition.name}")

        # Build tools first
        tools = []
        if self.definition.tools:
            for tool_def in self.definition.tools:
                tool_builder = ToolBuilder(tool_def)
                if tool_builder.validate():
                    tools.append(tool_builder.build())
                else:
                    raise ValidationError(f"Tool validation failed for {tool_def.metadata.function.name}")

        # Parse output schema if provided
        output_schema = None
        if self.definition.output_schema:
            try:
                import json
                output_schema = json.loads(self.definition.output_schema)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid output schema JSON: {str(e)}")

        return Agent(name=self.definition.name,
                     system_message=self.definition.system_message,
                     llm_config=self.llm_config,
                     tools=tools if tools else None,
                     use_tools=self.definition.use_tools,
                     keep_history=self.definition.keep_history,
                     output_schema=output_schema,
                     strict=self.definition.strict)


class SupervisorBuilder:

    def __init__(self, supervisor_definition: SupervisorDefinition, llm_config: Dict[str, str]):
        self.definition = supervisor_definition
        self.llm_config = llm_config

    def validate(self) -> bool:
        """
        Validate supervisor definition meets all requirements.
        
        Validates:
        1. Basic requirements (name, system message)
        2. Management structure
        3. Assistant supervisor constraints
        """
        try:
            # 1. Basic validation
            self._validate_basic_requirements()

            # 2. Management structure validation
            self._validate_management_structure()

            # 3. Assistant supervisor constraints
            self._validate_assistant_constraints()

            return True

        except ValidationError as e:
            print(f"Supervisor validation failed: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error in supervisor validation: {str(e)}")
            return False

    def _validate_basic_requirements(self):
        """Validate basic supervisor requirements"""
        if not self.definition.name or not self.definition.name.strip():
            raise ValidationError("Supervisor name cannot be empty")

        if not self.definition.system_message or not self.definition.system_message.strip():
            raise ValidationError("System message cannot be empty")

    def _validate_management_structure(self):
        """Validate management structure is consistent"""
        # Check for duplicate entries
        managed_components = (self.definition.managed_agents + self.definition.managed_assistant_supervisors)
        if len(set(managed_components)) != len(managed_components):
            raise ValidationError("Duplicate component names in management structure")

    def _validate_assistant_constraints(self):
        """Validate assistant supervisor specific constraints"""
        if self.definition.is_assistant:
            # Assistant supervisors shouldn't manage other assistant supervisors
            if self.definition.managed_assistant_supervisors:
                raise ValidationError("Assistant supervisors cannot manage other assistant supervisors")

    def build(self, id_) -> Supervisor:
        """Build supervisor if validation passes"""
        if not self.validate():
            raise ValidationError(f"Validation failed for supervisor {self.definition.name}")

        return Supervisor(name=self.definition.name,
                          system_message=self.definition.system_message,
                          llm_config=self.llm_config,
                          is_assistant=self.definition.is_assistant,
                          workflow_id=id_)


class WorkflowBuilder:

    def __init__(self,
                 agents_system_messages,
                 workflow_definition: WorkflowDefinition,
                 llm_config: Dict[str, str],
                 workflow_id: str = "000"):
        self.definition = workflow_definition
        self.llm_config = llm_config
        self.components = {}  # Store built components
        if agents_system_messages:

            self._update_system_messages(agents_system_messages)
        self.workflow_id = workflow_id

    def _update_system_messages(self, agent_messages: Dict[str, str]):
        """Update system messages in the workflow definition"""
        # Update main supervisor
        if self.definition.main_supervisor.name in agent_messages:
            self.definition.main_supervisor.system_message = agent_messages[self.definition.main_supervisor.name]

        # Update assistant supervisors
        for supervisor in self.definition.assistant_supervisors:
            if supervisor.name in agent_messages:
                supervisor.system_message = agent_messages[supervisor.name]

        # Update agents
        for agent in self.definition.agents:
            if agent.name in agent_messages:
                agent.system_message = agent_messages[agent.name]

    def build_component_and_validate(self) -> Supervisor:
        """Build and validate all components, then assemble the workflow"""
        # 1. Build and validate main supervisor
        main_sup_builder = SupervisorBuilder(self.definition.main_supervisor, self.llm_config)
        if main_sup_builder.validate():
            main_supervisor = main_sup_builder.build(self.workflow_id)
            self.components['main_supervisor'] = main_supervisor

        # 2. Build and validate assistant supervisors
        for asst_sup_def in self.definition.assistant_supervisors:
            asst_sup_builder = SupervisorBuilder(asst_sup_def, self.llm_config)
            if asst_sup_builder.validate():
                asst_supervisor = asst_sup_builder.build(self.workflow_id)
                self.components[asst_sup_def.name] = asst_supervisor

        # 3. Build and validate agents
        for agent_def in self.definition.agents:
            agent_builder = AgentBuilder(agent_def, self.llm_config)
            if agent_builder.validate():
                agent = agent_builder.build()
                self.components[agent_def.name] = agent

        # 4. Connect components based on management structure
        self._connect_components()

        return self.components['main_supervisor']

    def _connect_components(self):
        """
        Connect all components based on management structure.
        Ensures agents are only registered with their designated supervisors.
        """
        # 1. First, connect assistant supervisors with their agents
        for asst_sup_def in self.definition.assistant_supervisors:
            asst_sup = self.components[asst_sup_def.name]
            for agent_name in asst_sup_def.managed_agents:
                if agent_name not in self.components:
                    raise ValueError(f"Agent {agent_name} not found for assistant supervisor {asst_sup_def.name}")
                asst_sup.register_agent(self.components[agent_name])

        # 2. Then, connect components to main supervisor
        main_sup = self.components['main_supervisor']

        # a. Connect direct agents (only those specifically managed by main supervisor)
        for agent_name in self.definition.main_supervisor.managed_agents:
            if agent_name not in self.components:
                raise ValueError(f"Agent {agent_name} not found for main supervisor")
            main_sup.register_agent(self.components[agent_name])

        # b. Connect assistant supervisors to main supervisor
        for asst_sup_name in self.definition.main_supervisor.managed_assistant_supervisors:
            if asst_sup_name not in self.components:
                raise ValueError(f"Assistant supervisor {asst_sup_name} not found")
            main_sup.register_agent(self.components[asst_sup_name])

    def save_workflow_to_file(self, output_path: str) -> None:
        """
        Save the workflow implementation to a Python file.
        
        Args:
            output_path (str): Path where the Python file should be saved
        """
        try:
            with open(output_path, 'w') as file:
                # Write imports
                file.write('''import os
import json  # Added for output schema parsing
from dotenv import load_dotenv
from primisai.nexus.core import Agent, Supervisor

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}
    ''')

                # Write tool functions and their metadata
                file.write("\n# Tool Definitions\n")
                tool_definitions = self._generate_tool_definitions()
                file.write(tool_definitions)

                # Write agent creation
                file.write("\n# Agent Definitions\n")
                agent_definitions = self._generate_agent_definitions()
                file.write(agent_definitions)

                # Write assistant supervisor creation
                file.write("\n# Assistant Supervisor Definitions\n")
                asst_sup_definitions = self._generate_assistant_supervisor_definitions()
                file.write(asst_sup_definitions)

                # Write main supervisor creation and component registration
                file.write("\n# Main Supervisor Definition and Component Registration\n")
                main_sup_definition = self._generate_main_supervisor_definition()
                file.write(main_sup_definition)

                # Write main execution block
                file.write('''
if __name__ == "__main__":
    # Display the workflow structure
    print("\\nGenerated Workflow Structure:")
    main_supervisor.display_agent_graph()
    
    # Start interactive session
    print("\\nStarting interactive session. Type 'exit' to end.")
    while True:
        user_input = input("\\nUser: ").strip()
        if user_input.lower() == "exit":
            break
        
        try:
            response = main_supervisor.chat(user_input)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")
    ''')

            print(f"Workflow implementation saved to {output_path}")

        except Exception as e:
            raise Exception(f"Error saving workflow to file: {str(e)}")

    def _generate_tool_definitions(self) -> str:
        """Generate code for tool definitions."""
        tool_code = []
        tool_vars = []  # To keep track of tool variable names

        for agent_def in self.definition.agents:
            if agent_def.tools:
                for tool in agent_def.tools:
                    # Add tool function implementation
                    tool_code.append(tool.implementation)

                    # Add tool metadata
                    tool_name = tool.metadata.function.name
                    metadata_var = f"{tool_name}_metadata"
                    tool_vars.append((tool_name, metadata_var))

                    metadata_code = f'''
{metadata_var} = {{
    "type": "{tool.metadata.type}",
    "function": {{
        "name": "{tool.metadata.function.name}",
        "description": "{tool.metadata.function.description}",
        "parameters": {{
            "type": "{tool.metadata.function.parameters.type}",
            "properties": {{'''

                # Add properties
                for prop in tool.metadata.function.parameters.properties:
                    metadata_code += f'''
                "{prop.argument}": {{"type": "{prop.type}", "description": "{prop.description}"}},'''

                metadata_code += f'''
            }},
            "required": {tool.metadata.function.parameters.required}
        }}
    }}
}}

{tool_name}_tool = {{"tool": {tool_name}, "metadata": {metadata_var}}}
    '''
                tool_code.append(metadata_code)

        return "\n".join(tool_code)

    def _generate_agent_definitions(self) -> str:
        """Generate code for agent definitions."""
        agent_code = []

        for agent_def in self.definition.agents:
            tools_list = []
            if agent_def.tools:
                tools_list = [f"{tool.metadata.function.name}_tool" for tool in agent_def.tools]

            # Format output schema if provided
            output_schema_str = (f"json.loads('''{agent_def.output_schema}''')" if agent_def.output_schema else "None")

            agent_code.append(f'''
{agent_def.name.lower()} = Agent(
    name="{agent_def.name}",
    system_message="""{agent_def.system_message}""",
    llm_config=llm_config,
    tools=[{", ".join(tools_list)}] if {bool(tools_list)} else None,
    use_tools={agent_def.use_tools},
    keep_history={agent_def.keep_history},
    output_schema={output_schema_str},
    strict={agent_def.strict}
)''')

        return "\n".join(agent_code)

    def _generate_assistant_supervisor_definitions(self) -> str:
        """Generate code for assistant supervisor definitions."""
        sup_code = []

        for sup_def in self.definition.assistant_supervisors:
            sup_code.append(f'''
{sup_def.name.lower()} = Supervisor(
    name="{sup_def.name}",
    system_message="""{sup_def.system_message}""",
    llm_config=llm_config,
    is_assistant=True
)

# Register agents with {sup_def.name}
{" ".join(f'{sup_def.name.lower()}.register_agent({agent_name.lower()});' 
        for agent_name in sup_def.managed_agents)}
''')

        return "\n".join(sup_code)

    def _generate_main_supervisor_definition(self) -> str:
        """Generate code for main supervisor definition and final registration."""
        main_sup_def = self.definition.main_supervisor

        code = f'''
main_supervisor = Supervisor(
    name="{main_sup_def.name}",
    system_message="""{main_sup_def.system_message}""",
    llm_config=llm_config,
    is_assistant=False
)

# Register direct agents with main supervisor
{" ".join(f'main_supervisor.register_agent({agent_name.lower()});' 
        for agent_name in main_sup_def.managed_agents)}

# Register assistant supervisors with main supervisor
{" ".join(f'main_supervisor.register_agent({sup_name.lower()});' 
        for sup_name in main_sup_def.managed_assistant_supervisors)}
'''

        return code
