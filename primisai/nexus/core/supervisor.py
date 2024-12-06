"""
Supervisor module for managing multiple specialized AI agents.

This module provides a Supervisor class that coordinates interactions between
users and multiple specialized AI agents.
"""

import json
from typing import List, Dict, Any, Optional, Union
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core import AI
from primisai.nexus.core import Agent
from primisai.nexus.utils.debugger import Debugger


class Supervisor(AI):
    """
    A Supervisor class that manages multiple specialized AI agents.

    This class handles user queries, delegates tasks to appropriate agents,
    and coordinates complex multi-step processes.
    """

    def __init__(self, name: str, llm_config: Dict[str, str], system_message: Optional[str] = None, use_agents: bool=True):
        """
        Initialize the Supervisor instance.

        Args:
            name (str): The name of the supervisor.
            llm_config (Dict[str, str]): Configuration for the language model.
            system_message (Optional[str]): The initial system message for the agent.
            use_agents (bool): Whether to use agents or not.

        Raises:
            ValueError: If the name is empty.
        """
        super().__init__(llm_config=llm_config)

        if not name:
            raise ValueError("Supervisor name cannot be empty")

        self.name = name
        self.system_message = system_message if system_message is not None else self._get_default_system_message()
        self.registered_agents: List[Agent] = []
        self.available_tools: List[Dict[str, Any]] = []
        self.use_agents = use_agents
        self.chat_history: List[Dict[str, str]] = [{'role': 'system', 'content': self.system_message}]
        self.debugger = Debugger(name=self.name)
        self.debugger.start_session()

    @staticmethod
    def _get_default_system_message() -> str:
        """Return the default system message for the Supervisor."""
        return """You are a highly capable user assistant and the Supervisor of multiple specialized agents. Your primary responsibilities include:
1. Understanding user queries and determining which agent(s) can best address them.
2. Carefully planning the sequence of agent calls to ensure relevance.
3. Passing outputs from one agent as inputs to another when necessary.
4. Calling agents sequentially to execute complex tasks in a coordinated manner."""

    def configure_system_prompt(self, system_prompt: str) -> None:
        """
        Configure the system prompt for the Supervisor.

        Args:
            system_prompt (str): The new system prompt to set.
        """
        self.system_message = {"role": "system", "content": system_prompt}

    def register_agent(self, agent: Union['Agent', 'Supervisor']) -> None:
        """
        Register a new agent with the Supervisor.

        Args:
            agent (Union[Agent, Supervisor]): The agent or supervisor to register.
        """
        self.registered_agents.append(agent)
        self._add_agent_tool(agent)
        # self.system_message += f"{agent.name}: {agent.system_message}\n"

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
                        "agent_instruction": {
                            "type": "string",
                            "description": f"Instructions for the {agent.name} agent."
                        },
                        "thinking_process": {
                            "type": "string",
                            "description": "Explanation of the decision-making process."
                        }
                    },
                    "required": ["agent_instruction", "thinking_process"]
                }
            }
        })

    def get_registered_agents(self) -> List[str]:
        """
        Get the names of all registered agents.

        Returns:
            List[str]: A list of registered agent names.
        """
        return [agent.name for agent in self.registered_agents]

    def delegate_to_agent(self, message: ChatCompletionMessage) -> str:
        """
        Delegate a task to the appropriate agent based on the supervisor's response.

        Args:
            message (ChatCompletionMessage): The message containing the delegation information.

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
        agent_instruction = args.get('agent_instruction')
        thinking_process = args.get('thinking_process')

        if not agent_instruction:
            raise ValueError("Agent instruction is missing from the function call")

        self.debugger.log(f"Agent: {target_agent_name} | Instruction: {agent_instruction} | Thinking: {thinking_process}")

        for agent in self.registered_agents:
            if agent.name.lower() == target_agent_name:
                agent_response = agent.chat(query=agent_instruction)
                self.debugger.log(f"{target_agent_name}: {agent_response}")
                return agent_response

        raise ValueError(f"No agent found with name '{target_agent_name}'")

    def chat(self, query: str) -> str:
        """
        Process user input and generate a response using the appropriate agents.

        Args:
            query (str): The user's input query.

        Returns:
            str: The final response to the user's query.

        Raises:
            RuntimeError: If there's an error in processing the user input.
        """
        self.debugger.log(f"User: {query}")
        self.chat_history.append({'role': 'user', 'content': query})

        try:
            while True:
                supervisor_response = self.generate_response(self.chat_history, tools=self.available_tools, use_tools=self.use_agents).choices[0]

                if supervisor_response.finish_reason == "stop":
                    query_answer = supervisor_response.message.content
                    self.debugger.log(f"{self.name}: {query_answer}")
                    self.chat_history.append({"role": "assistant", "content": query_answer})
                    return query_answer

                self.chat_history.append(supervisor_response.message)

                # Check if tool_calls attribute exists
                if hasattr(supervisor_response.message, 'tool_calls') and supervisor_response.message.tool_calls:
                    agent_feedback = self.delegate_to_agent(supervisor_response.message)
                    self.chat_history.append({
                        "role": "tool",
                        "content": agent_feedback,
                        "tool_call_id": supervisor_response.message.tool_calls[0].id
                    })
                else:
                    # If no tool_calls, treat it as a direct response
                    return supervisor_response.message.content

        except Exception as e:
            error_msg = f"Error in processing user input: {str(e)}"
            self.debugger.log(error_msg)
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
        """Reset the chat history to its initial state with only the system message."""
        self.chat_history = [{'role': 'system', 'content': self.system_message}]

    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get the current chat history.

        Returns:
            List[Dict[str, str]]: The current chat history.
        """
        return self.chat_history

    def add_to_chat_history(self, role: str, content: str) -> None:
        """
        Add a new message to the chat history.

        Args:
            role (str): The role of the message sender (e.g., 'user', 'assistant', 'system').
            content (str): The content of the message.

        Raises:
            ValueError: If an invalid role is provided.
        """
        if role not in ['user', 'assistant', 'system', 'tool']:
            raise ValueError(f"Invalid role: {role}")
        self.chat_history.append({"role": role, "content": content})

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

    def display_agent_graph(self, indent=""):
        """
        Display a simple ASCII graph in the terminal showing the Supervisor,
        connected agents, sub-supervisors, and their available tools.
        """
        print(f"{indent}Supervisor: {self.name}")
        print(f"{indent}│")

        for i, agent in enumerate(self.registered_agents):
            is_last_agent = i == len(self.registered_agents) - 1
            agent_prefix = "└── " if is_last_agent else "├── "

            if isinstance(agent, Supervisor):
                print(f"{indent}{agent_prefix}Sub-Supervisor: {agent.name}")
                agent.display_agent_graph(indent + ("    " if is_last_agent else "│   "))
            else:
                print(f"{indent}{agent_prefix}Agent: {agent.name}")

                if hasattr(agent, 'tools') and agent.tools:
                    tool_indent = indent + ("    " if is_last_agent else "│   ")
                    for j, tool in enumerate(agent.tools):
                        is_last_tool = j == len(agent.tools) - 1
                        tool_prefix = "└── " if is_last_tool else "├── "
                        tool_name = tool['metadata']['function']['name'] if 'metadata' in tool else "Unnamed Tool"
                        print(f"{tool_indent}{tool_prefix}Tool: {tool_name}")
                else:
                    print(f"{indent}{'    ' if is_last_agent else '│   '}└── No tools available")

            if not is_last_agent:
                print(f"{indent}│")
