"""
Agent module for handling specialized AI interactions.

This module provides an Agent class that extends the base AI functionality
with additional features like tool usage and chat history management.
"""

import json
from typing import List, Dict, Optional, Any
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core.ai import AI
from primisai.nexus.history import HistoryManager, EntityType
from primisai.nexus.utils.debugger import Debugger


class Agent(AI):
    """
    An Agent class that extends the base AI functionality.

    This class handles specialized interactions, including the use of tools
    and management of chat history. It can operate independently or as part
    of a supervised workflow.
    """

    def __init__(self,
                 name: str,
                 llm_config: Dict[str, str],
                 workflow_id: Optional[str] = None,
                 tools: Optional[List[Dict[str, Any]]] = None,
                 system_message: Optional[str] = None,
                 use_tools: bool = False,
                 keep_history: bool = True):
        """
        Initialize the Agent instance.

        Args:
            name (str): The name of the agent.
            llm_config (Dict[str, str]): Configuration for the language model.
            workflow_id (Optional[str]): ID of the workflow. Will be set when registered with a Supervisor.
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
        self.workflow_id = workflow_id
        self.use_tools = use_tools
        self.tools = tools or []
        self.tools_metadata = [tool['metadata'] for tool in self.tools]
        self.system_message = system_message
        self.keep_history = keep_history
        self.history_manager = None
        self.debugger = Debugger(name=name)
        self.debugger.start_session()
        self.chat_history: List[Dict[str, str]] = []

        if system_message:
            self.set_system_message(system_message)

    def set_workflow_id(self, workflow_id: str) -> None:
        """
        Set the workflow ID and initialize the history manager.
        This method is called by the Supervisor when registering the agent.

        Args:
            workflow_id (str): The workflow ID to set.
        """
        self.workflow_id = workflow_id
        self.history_manager = HistoryManager(workflow_id)
        
        if self.system_message:
            self.history_manager.append_message(
                message={"role": "system", "content": self.system_message},
                sender_type=EntityType.AGENT,
                sender_name=self.name
            )

    def set_system_message(self, message: str) -> None:
        """
        Set the system message for the agent.

        Args:
            message (str): The system message to set.
        """
        self.system_message = message
        self._reset_chat_history()

    def chat(self, query: str, sender_name: Optional[str] = None) -> str:
        """
        Process a chat interaction with the agent.

        Args:
            query (str): The query to process.
            sender_name (Optional[str]): Name of the entity sending the query.
                                       Could be a supervisor name or None for direct interactions.

        Returns:
            str: The agent's response to the query.

        Raises:
            RuntimeError: If there's an error processing the query or using tools.
        """
        self.debugger.log(f"Query received from {sender_name or 'direct'}: {query}")
        
        if not self.keep_history:
            self._reset_chat_history()
        
        user_msg = {'role': 'user', 'content': query}
        self.chat_history.append(user_msg)
        
        query_msg_id = None
        if self.history_manager:
            sender_type = (EntityType.MAIN_SUPERVISOR if sender_name 
                         else EntityType.USER)
            query_msg_id = self.history_manager.append_message(
                message=user_msg,
                sender_type=sender_type,
                sender_name=sender_name or "user"
            )

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
                                        
                    response_msg = {"role": "assistant", "content": user_query_answer}
                    self.chat_history.append(response_msg)
                    
                    if self.history_manager:
                        self.history_manager.append_message(
                            message=response_msg,
                            sender_type=EntityType.AGENT,
                            sender_name=self.name,
                            parent_id=query_msg_id
                        )
                    return user_query_answer
                
                tool_call = response.message.tool_calls[0]
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
                
                tool_msg_id = None
                if self.history_manager:
                    tool_msg_id = self.history_manager.append_message(
                        message=tool_msg,
                        sender_type=EntityType.AGENT,
                        sender_name=self.name,
                        parent_id=query_msg_id,
                        tool_call_id=tool_call.id
                    )

                self._process_tool_call(response.message, tool_msg_id)

            except Exception as e:
                error_msg = f"Error in chat processing: {str(e)}"
                self.debugger.log(error_msg)
                raise RuntimeError(error_msg)

    def _process_tool_call(self, message: ChatCompletionMessage, parent_msg_id: Optional[str] = None) -> None:
        """
        Process a tool call from the chat response.

        Args:
            message (ChatCompletionMessage): The message containing the tool call.
            parent_msg_id (Optional[str]): ID of the parent message in history.

        Raises:
            ValueError: If the specified tool is not found or if there's an error in processing arguments.
        """
        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            raise ValueError("Message does not contain tool calls")
        
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

        target_tool = next((tool for tool in self.tools 
                           if tool['metadata']['function']['name'] == target_tool_name), None)

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
            
            tool_response_msg = {
                "role": "tool",
                "content": str(tool_feedback),
                "tool_call_id": function_call.id
            }
            self.chat_history.append(tool_response_msg)
            
            if self.history_manager:
                self.history_manager.append_message(
                    message=tool_response_msg,
                    sender_type=EntityType.TOOL,
                    sender_name=target_tool_name,
                    parent_id=parent_msg_id,
                    tool_call_id=function_call.id
                )
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.debugger.log(error_msg, level="error")
            raise RuntimeError(error_msg) from e
        
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get the current chat history.

        Returns:
            List[Dict[str, str]]: The current chat history.
        """
        return self.chat_history
        
    def _reset_chat_history(self) -> None:
        """Reset chat history to initial state (system message only)."""
        self.chat_history = []
        if self.system_message:
            system_msg = {"role": "system", "content": self.system_message}
            self.chat_history = [system_msg]
            
            if self.history_manager:
                self.history_manager.append_message(
                    message=system_msg,
                    sender_type=EntityType.AGENT,
                    sender_name=self.name
                )

    def __str__(self) -> str:
        """Return a string representation of the Agent instance."""
        return f"Agent(name={self.name}, use_tools={self.use_tools})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the Agent instance."""
        return (f"Agent(name={self.name}, llm_config={self.llm_config}, "
                f"use_tools={self.use_tools}, tool_count={len(self.tools)})")
