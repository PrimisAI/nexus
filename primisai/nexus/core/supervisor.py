"""
Supervisor module for managing multiple specialized AI agents.

This module provides a Supervisor class that coordinates interactions between
users and multiple specialized AI agents.
"""

import json, uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core import AI
from primisai.nexus.core import Agent
from primisai.nexus.history import HistoryManager, EntityType
from primisai.nexus.utils import Debugger


class Supervisor(AI):
    """
    A Supervisor class that manages multiple specialized AI agents.

    This class handles user queries, delegates tasks to appropriate agents,
    and coordinates complex multi-step processes.
    
    The Supervisor can operate in two modes:
    1. Main Supervisor: Creates and manages the workflow directory
    2. Assistant Supervisor: Works within an existing workflow
    """

    def __init__(self, 
                 name: str, 
                 llm_config: Dict[str, str], 
                 workflow_id: Optional[str] = None,
                 is_assistant: bool = False,
                 system_message: Optional[str] = None, 
                 use_agents: bool = True):
        """
        Initialize the Supervisor instance.

        Args:
            name (str): The name of the supervisor.
            llm_config (Dict[str, str]): Configuration for the language model.
            workflow_id (Optional[str]): ID for the workflow. Only used by main supervisor.
            is_assistant (bool): Whether this is an assistant supervisor.
            system_message (Optional[str]): The initial system message for the agent.
            use_agents (bool): Whether to use agents or not.

        Raises:
            ValueError: If the name is empty or if workflow management rules are violated.
        """
        super().__init__(llm_config=llm_config)

        if not name:
            raise ValueError("Supervisor name cannot be empty")

        self.name = name
        self.is_assistant = is_assistant
        self.workflow_id = workflow_id
        
        self._pending_registrations: List[Union[Agent, 'Supervisor']] = []
        self.system_message = system_message if system_message is not None else self._get_default_system_message()
        
        if not is_assistant:
            if workflow_id:
                try:
                    self.history_manager = HistoryManager(workflow_id)
                except:
                    self._initialize_workflow()
                    self.history_manager = HistoryManager(workflow_id)
                if not self.history_manager.has_system_message(self.name):
                    self._initialize_chat_history()
            else:
                self._initialize_workflow()
                self.history_manager = HistoryManager(self.workflow_id)
                self._initialize_chat_history()
        else:
            self.history_manager = None
        
        self.registered_agents: List[Union[Agent, 'Supervisor']] = []
        self.available_tools: List[Dict[str, Any]] = []
        self.use_agents = use_agents
        
        self.chat_history: List[Dict[str, str]] = []
        
        self.debugger = Debugger(name=self.name, workflow_id=self.workflow_id)
        self.debugger.start_session()

    def _get_default_system_message(self) -> str:
        """
        Get the default system message based on supervisor type.

        Returns:
            str: Appropriate system message for the supervisor type.
        """
        if self.is_assistant:
            return """You are an Assistant Supervisor, part of a larger workflow managed by the Main Supervisor. 
            Your role is to handle specialized tasks delegated to you and manage your assigned agents effectively."""
        else:
            return """You are the Main Supervisor, responsible for managing the entire workflow. 
            Your tasks include coordinating with Assistant Supervisors and direct agents, ensuring efficient task delegation 
            and execution."""

    def _initialize_chat_history(self) -> None:
        """Initialize chat history with system message and record in history manager."""
        if self.system_message:
            system_msg = {'role': 'system', 'content': self.system_message}
            self.chat_history = [system_msg]
            
            if self.history_manager:
                self.history_manager.append_message(
                    message=system_msg,
                    sender_type=EntityType.MAIN_SUPERVISOR if not self.is_assistant
                            else EntityType.ASSISTANT_SUPERVISOR,
                    sender_name=self.name
                )

    def configure_system_prompt(self, system_prompt: str) -> None:
        """
        Configure the system prompt for the Supervisor.

        Args:
            system_prompt (str): The new system prompt to set.
        """
        self.system_message = {"role": "system", "content": system_prompt}

    def register_agent(self, agent: Union[Agent, 'Supervisor']) -> None:
        """
        Register a new agent or assistant supervisor.

        Args:
            agent (Union[Agent, Supervisor]): The agent or assistant supervisor to register.

        Raises:
            ValueError: If attempting to register a main supervisor or if registration rules are violated.
        """
        
        if isinstance(agent, Supervisor) and not agent.is_assistant:
            raise ValueError("Only assistant supervisors can be registered as agents")

        if self.is_assistant and not self.workflow_id:
            self._pending_registrations.append(agent)
            return
        
        if isinstance(agent, Supervisor):
            agent.set_workflow_id(self.workflow_id)
        else:
            agent.set_workflow_id(self.workflow_id)
        
        self.registered_agents.append(agent)
        self._add_agent_tool(agent)
        # self.system_message += f"{agent.name}: {agent.system_message}\n"
    
    def set_workflow_id(self, workflow_id: str) -> None:
        """
        Set the workflow ID for this supervisor.
        
        Args:
            workflow_id (str): The workflow ID to set.
        """
        self.workflow_id = workflow_id
        self.debugger.update_workflow_id(workflow_id)
        self.history_manager = HistoryManager(workflow_id)
        self._initialize_chat_history()
        self._process_pending_registrations()
        
    def _process_pending_registrations(self) -> None:
        """Process any pending agent registrations."""
        if self._pending_registrations:
            for agent in self._pending_registrations:
                self.register_agent(agent)
            self._pending_registrations.clear()

    def _add_agent_tool(self, agent: Agent) -> None:
        """
        Add a tool for the registered agent to the available tools.

        Args:
            agent (Agent): The agent for which to add a tool.
        """
        self.available_tools.append({
            "type": "function",
            "function": {
                "name": f"delegate_to_{agent.name}",
                "description": agent.system_message,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": (
                                f"Supervisor's reasoning for choosing the {agent.name} agent. "
                                "Explain why this agent is being invoked and what is expected of it."
                            )
                        },
                        "query": {
                            "type": "string",
                            "description": (
                                f"The actual query or instruction for {agent.name} agent to respond to."
                            )
                        },
                        "context": {
                            "type": "string",
                            "description": (
                                "All relevant background information, prior facts, decisions, "
                                "and state needed by the agent to solve the current query. "
                                "Should be as detailed and self-contained as possible."
                            )
                        },
                    },
                    "required": ["reasoning", "query", "context"]
                }
            },
            "strict": True,
        })
        
    def _initialize_workflow(self) -> None:
        """
        Initialize the workflow directory and set up necessary structures.
        Only called by main supervisor.

        Raises:
            ValueError: If an assistant supervisor attempts to initialize a workflow.
        """
        if self.is_assistant:
            raise ValueError("Assistant supervisors cannot initialize workflows")
        
        if not self.workflow_id:
            self.workflow_id = str(uuid.uuid4())
        
        workflow_path = Path("nexus_workflows") / self.workflow_id
        workflow_path.mkdir(parents=True, exist_ok=True)
        
        history_file = workflow_path / "history.jsonl"
        if not history_file.exists():
            history_file.touch()

    def get_registered_agents(self) -> List[str]:
        """
        Get the names of all registered agents.

        Returns:
            List[str]: A list of registered agent names.
        """
        return [agent.name for agent in self.registered_agents]

    def delegate_to_agent(self, 
                          message: ChatCompletionMessage,
                          parent_msg_id: str,
                          supervisor_chain: Optional[List[str]] = None) -> str:
        """
        Delegate a task to the appropriate agent based on the supervisor's response.

        Args:
            message (ChatCompletionMessage): The message containing the delegation information.
            parent_msg_id (str): ID of the parent message in history.
            supervisor_chain (Optional[List[str]]): Chain of supervisors involved in delegation.

        Returns:
            str: The response from the delegated agent.

        Raises:
            ValueError: If no matching agent is found for delegation or if the message structure is unexpected.
        """
        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            raise ValueError("Message does not contain tool calls")

        function_call = message.tool_calls[0]
        target_agent_name = function_call.function.name.replace("delegate_to_", "").lower()
        args = json.loads(function_call.function.arguments)
        reasoning = args.get('reasoning')
        context = args.get('context')
        query = args.get('query')

        if not query:
            raise ValueError("Query is missing from the function call")

        self.debugger.log(f"[DELEGATION] Agent: {target_agent_name}")
        self.debugger.log(f"[REASONING] {reasoning}")
        self.debugger.log(f"[CONTEXT] {context}")
        self.debugger.log(f"[QUERY] {query}")
        
        current_chain = supervisor_chain or []
        current_chain.append(self.name)

        for agent in self.registered_agents:
            if agent.name.lower() == target_agent_name:
                agent_response = agent.chat(
                    query=f"CONTEXT:\n{context}\n\nQUERY:\n{query}",
                    sender_name=self.name
                )
                self.debugger.log(f"[RESPONSE] {target_agent_name}: {agent_response}")
                return agent_response

        raise ValueError(f"No agent found with name '{target_agent_name}'")

    def chat(self, 
             query: str,
             sender_name: Optional[str] = None,
             supervisor_chain: Optional[List[str]] = None) -> str:
        """
        Process user input and generate a response using the appropriate agents.

        Args:
            query (str): The user's input query.
            sender_name (Optional[str]): Name of the sender (for assistant supervisors).
            supervisor_chain (Optional[List[str]]): Chain of supervisors in delegation.

        Returns:
            str: The final response to the user's query.

        Raises:
            RuntimeError: If there's an error in processing the user input.
        """
        self.debugger.log(f"[USER INPUT] {query}")
        
        current_chain = supervisor_chain or []
        if self.name not in current_chain:
            current_chain.append(self.name)
        
        user_msg = {'role': 'user', 'content': query}
        self.chat_history.append(user_msg)

        user_msg_id = self.history_manager.append_message(
            message=user_msg,
            sender_type=EntityType.MAIN_SUPERVISOR if sender_name else EntityType.USER,
            sender_name=sender_name or "user",
            supervisor_chain=current_chain
        )

        try:
            while True:
                supervisor_response = self.generate_response(self.chat_history, tools=self.available_tools, use_tools=self.use_agents).choices[0]

                if not supervisor_response.finish_reason == "tool_calls":
                    query_answer = supervisor_response.message.content
                    self.debugger.log(f"[SUPERVISOR RESPONSE] {query_answer}")
                    
                    response_msg = {"role": "assistant", "content": query_answer}
                    self.chat_history.append(response_msg)
                    
                    self.history_manager.append_message(
                        message=response_msg,
                        sender_type=EntityType.MAIN_SUPERVISOR if not self.is_assistant 
                                    else EntityType.ASSISTANT_SUPERVISOR,
                        sender_name=self.name,
                        parent_id=user_msg_id,
                        supervisor_chain=current_chain
                    )
                    
                    return query_answer

                tool_call = supervisor_response.message.tool_calls[0]
                tool_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        'id': tool_call.id,
                        'type': 'function',
                        'function': {
                            'name': tool_call.function.name,
                            'arguments': tool_call.function.arguments
                        }
                    }]
                }
                self.chat_history.append(tool_msg)
                
                tool_msg_id = self.history_manager.append_message(
                    message=tool_msg,
                    sender_type=EntityType.MAIN_SUPERVISOR if not self.is_assistant 
                                else EntityType.ASSISTANT_SUPERVISOR,
                    sender_name=self.name,
                    parent_id=user_msg_id,
                    tool_call_id=tool_call.id,
                    supervisor_chain=current_chain
                )
                
                if hasattr(supervisor_response.message, 'tool_calls') and supervisor_response.message.tool_calls:
                    agent_feedback = self.delegate_to_agent(
                    supervisor_response.message,
                    tool_msg_id,
                    supervisor_chain=current_chain
                )
                    feedback_msg = {
                        "role": "tool",
                        "content": agent_feedback,
                        "tool_call_id": tool_call.id
                    }
                    self.chat_history.append(feedback_msg)
                    
                    self.history_manager.append_message(
                        message=feedback_msg,
                        sender_type=EntityType.TOOL,
                        sender_name=self.name,
                        parent_id=tool_msg_id,
                        tool_call_id=tool_call.id,
                        supervisor_chain=current_chain
                    )
                else:
                    return supervisor_response.message.content

        except Exception as e:
            error_msg = f"Error in processing user input: {str(e)}"
            self.debugger.log(f"[ERROR] {error_msg}", level="error")
            raise RuntimeError(error_msg)

    def start_interactive_session(self) -> None:
        """
        Start an interactive session with the user.

        This method initiates a loop that continuously processes user input
        until the user decides to exit.
        """
        print("Starting interactive session. Type 'exit' to end the session.")
        while True:
            user_input = input("User: ").strip()
            if user_input.lower() == "exit":
                print("Ending session. Goodbye!")
                break
            try:
                supervisor_output = self.chat(query=user_input)
                print(f"Supervisor: {supervisor_output}")
            except Exception as e:
                print(f"An error occurred: {str(e)}")

    def __str__(self) -> str:
        """Return a string representation of the Supervisor instance."""
        return f"Supervisor(name={self.name}, agents={len(self.registered_agents)})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the Supervisor instance."""
        return (f"Supervisor(name={self.name}, llm_config={self.llm_config}, "
                f"registered_agents={[agent.name for agent in self.registered_agents]})")

    def reset_chat_history(self) -> None:
        """Reset chat history to initial state and clear history manager."""
        self.history_manager.clear_history()
        self._initialize_chat_history()

    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get the current chat history.

        Returns:
            List[Dict[str, str]]: The current chat history.
        """
        return self.chat_history

    def add_to_chat_history(self, role: str, content: str) -> None:
        """
        Add a new message to both chat history and history manager.

        Args:
            role (str): The role of the message sender (e.g., 'user', 'assistant', 'system').
            content (str): The content of the message.

        Raises:
            ValueError: If an invalid role is provided.
        """
        if role not in ['user', 'assistant', 'system', 'tool']:
            raise ValueError(f"Invalid role: {role}")
        
        message = {"role": role, "content": content}
        self.chat_history.append(message)
        
        sender_type = {
            'user': EntityType.USER,
            'assistant': EntityType.MAIN_SUPERVISOR if not self.is_assistant 
                        else EntityType.ASSISTANT_SUPERVISOR,
            'system': EntityType.MAIN_SUPERVISOR if not self.is_assistant 
                     else EntityType.ASSISTANT_SUPERVISOR,
            'tool': EntityType.TOOL
        }[role]
        
        self.history_manager.append_message(
            message=message,
            sender_type=sender_type,
            sender_name=self.name
        )

    def get_agent_by_name(self, agent_name: str) -> Optional[Agent]:
        """
        Get a registered agent by its name.

        Args:
            agent_name (str): The name of the agent to retrieve.

        Returns:
            Optional[Agent]: The agent with the specified name, or None if not found.
        """
        return next((agent for agent in self.registered_agents if agent.name.lower() == agent_name.lower()), None)

    def remove_agent(self, agent_name: str) -> bool:
        """
        Remove a registered agent by its name.

        Args:
            agent_name (str): The name of the agent to remove.

        Returns:
            bool: True if the agent was successfully removed, False otherwise.
        """
        agent = self.get_agent_by_name(agent_name)
        if agent:
            self.registered_agents.remove(agent)
            self.available_tools = [tool for tool in self.available_tools
                                    if tool['function']['name'] != f"delegate_to_{agent_name}"]
            return True
        return False

    def update_system_message(self) -> None:
        """
        Update the system message to reflect the current set of registered agents.
        """
        agent_descriptions = "\n".join(f"{agent.name}: {agent.system_message}" for agent in self.registered_agents)
        self.system_message = f"{self._get_default_system_message()}\n\n{agent_descriptions}"
        self.reset_chat_history()
        
    @property
    def is_main_supervisor(self) -> bool:
        """
        Check if this is the main supervisor.

        Returns:
            bool: True if this is the main supervisor, False if assistant.
        """
        return not self.is_assistant
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get information about the current workflow.

        Returns:
            Dict[str, Any]: Dictionary containing workflow information.
        """
        return {
            'workflow_id': self.workflow_id,
            'supervisor_type': 'main' if self.is_main_supervisor else 'assistant',
            'name': self.name,
            'registered_agents': [
                {
                    'name': agent.name,
                    'type': 'supervisor' if isinstance(agent, Supervisor) else 'agent'
                }
                for agent in self.registered_agents
            ]
        }

    def display_agent_graph(self, indent="", skip_header=False) -> None:
        """
        Display the supervisor-agent hierarchy.
        
        Args:
            indent (str): Current indentation level
            skip_header (bool): Whether to skip printing the supervisor header
        """
        if not skip_header:
            supervisor_type = "Main Supervisor" if self.is_main_supervisor else "Assistant Supervisor"
            print(f"{indent}{supervisor_type}: {self.name}")
            
            if self.registered_agents:
                print(f"{indent}│")
        
        for i, agent in enumerate(self.registered_agents):
            is_last_agent = i == len(self.registered_agents) - 1
            agent_prefix = "└── " if is_last_agent else "├── "
            current_indent = indent + ("    " if is_last_agent else "│   ")
            
            if isinstance(agent, Supervisor):
                print(f"{indent}{agent_prefix}Assistant Supervisor: {agent.name}")
                agent.display_agent_graph(current_indent, skip_header=True)  # Skip header for recursive calls
            else:
                print(f"{indent}{agent_prefix}Agent: {agent.name}")
                if hasattr(agent, 'tools') and agent.tools:
                    for j, tool in enumerate(agent.tools):
                        is_last_tool = j == len(agent.tools) - 1
                        tool_prefix = "└── " if is_last_tool else "├── "
                        tool_name = tool['metadata']['function']['name'] if 'metadata' in tool else "Unnamed Tool"
                        print(f"{current_indent}{tool_prefix}Tool: {tool_name}")
                else:
                    print(f"{current_indent}└── No tools available")
            
            if not is_last_agent and i < len(self.registered_agents) - 1:
                print(f"{indent}│")