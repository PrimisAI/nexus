"""
Agent module for handling specialized AI interactions.

This module provides an Agent class that extends the base AI functionality
with additional features like tool usage and chat history management.
"""

import json
from typing import List, Dict, Optional, Any
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core.ai import AI
from primisai.nexus.utils.debugger import Debugger


class Agent(AI):
    """
    An Agent class that extends the base AI functionality.

    This class handles specialized interactions, including the use of tools
    and management of chat history.
    """

    def __init__(self, name: str, llm_config: Dict[str, str],
                 tools: Optional[List[Dict[str, Any]]] = None,
                 system_message: Optional[str] = None,
                 use_tools: bool = False,
                 keep_history: bool = True):
        """
        Initialize the Agent instance.

        Args:
            name (str): The name of the agent.
            llm_config (Dict[str, str]): Configuration for the language model.
            tools (Optional[List[Dict[str, Any]]]): List of tools available to the agent.
            system_message (Optional[str]): The initial system message for the agent.
            use_tools (bool): Whether to use tools in interactions.
            keep_history (bool): Whether to maintain chat history between interactions.

        Raises:
            ValueError: If the name is empty or if tools are enabled but not provided.
        """
        super().__init__(llm_config=llm_config)

        if not name:
            raise ValueError("Agent name cannot be empty")
        if use_tools and not tools:
            raise ValueError("Tools must be provided when use_tools is True")

        self.name = name
        self.use_tools = use_tools
        self.tools = tools or []
        self.tools_metadata = [tool['metadata'] for tool in self.tools]
        self.system_message = system_message
        self.keep_history = keep_history
        self.debugger = Debugger(name=name)
        self.debugger.start_session()
        self.chat_history: List[Dict[str, str]] = []

        if system_message:
            self.set_system_message(system_message)

    def set_system_message(self, message: str) -> None:
        """
        Set the system message for the agent.

        Args:
            message (str): The system message to set.
        """
        self.system_message = message
        self._reset_chat_history()

    def chat(self, query: str) -> str:
        """
        Process a chat interaction with the agent.

        Args:
            query (str): The query to process.

        Returns:
            str: The agent's response to the query.

        Raises:
            RuntimeError: If there's an error processing the query or using tools.
        """
        self.debugger.log(f"Query received: {query}")
        
        if not self.keep_history:
            self._reset_chat_history()
        
        self.chat_history.append({'role': 'user', 'content': query})

        while True:
            try:
                response = self.generate_response(
                    self.chat_history,
                    tools=self.tools_metadata,
                    use_tools=self.use_tools
                ).choices[0]

                if not response.finish_reason == "tool_calls":
                    user_query_answer = response.message.content
                    self.debugger.log(f"{self.name} response: {user_query_answer}")
                    self.chat_history.append({"role": "assistant", "content": user_query_answer})
                    return user_query_answer

                self._process_tool_call(response.message)

            except Exception as e:
                error_msg = f"Error in chat processing: {str(e)}"
                self.debugger.log(error_msg)
                raise RuntimeError(error_msg)

    def _process_tool_call(self, message: ChatCompletionMessage) -> None:
        """
        Process a tool call from the chat response.

        Args:
            message (ChatCompletionMessage): The message containing the tool call.

        Raises:
            ValueError: If the specified tool is not found or if there's an error in processing arguments.
        """
        self.chat_history.append(message)
        function_call = message.tool_calls[0]
        target_tool_name = function_call.function.name
        
        self.debugger.log(f"Initiating tool call: {target_tool_name}")
        
        try:
            tool_arguments = json.loads(function_call.function.arguments)
            self.debugger.log(f"Tool arguments: {json.dumps(tool_arguments, indent=2)}")
        except json.JSONDecodeError:
            error_msg = f"Invalid JSON in function arguments: {function_call.function.arguments}"
            self.debugger.log(error_msg, level="error")
            raise ValueError(error_msg)

        target_tool = next((tool for tool in self.tools if tool['metadata']['function']['name'] == target_tool_name), None)

        if not target_tool:
            error_msg = f"Tool '{target_tool_name}' not found"
            self.debugger.log(error_msg, level="error")
            raise ValueError(error_msg)

        tool_function = target_tool['tool']
        
        try:
            if hasattr(tool_function, '__kwdefaults__'):
                tool_feedback = tool_function(**tool_arguments)
            else:
                tool_feedback = tool_function(tool_arguments)
            
            self.debugger.log(f"Tool execution successful")
            self.debugger.log(f"Tool response: {str(tool_feedback)}")
            
            self.chat_history.append({
                "role": "tool",
                "content": str(tool_feedback),
                "tool_call_id": function_call.id
            })
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.debugger.log(error_msg, level="error")
            raise RuntimeError(error_msg) from e
        
    def _reset_chat_history(self) -> None:
        """Reset chat history to initial state (system message only)."""
        if self.system_message:
            self.chat_history = [{"role": "system", "content": self.system_message}]
        else:
            self.chat_history = []

    def __str__(self) -> str:
        """Return a string representation of the Agent instance."""
        return f"Agent(name={self.name}, use_tools={self.use_tools})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the Agent instance."""
        return (f"Agent(name={self.name}, llm_config={self.llm_config}, "
                f"use_tools={self.use_tools}, tool_count={len(self.tools)})")
