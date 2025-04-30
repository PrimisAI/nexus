"""
Agent module for handling specialized AI interactions.

This module provides an Agent class that extends the base AI functionality
with additional features like tool usage and chat history management.
"""

import json, asyncio
from typing import List, Dict, Optional, Any
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core.ai import AI
from primisai.nexus.history import HistoryManager, EntityType
from primisai.nexus.utils import Debugger
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client


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
                 keep_history: bool = True,
                 mcp_servers: Optional[List[Dict[str, Any]]] = None,
                 output_schema: Optional[Dict[str, Any]] = None,
                 strict: bool = False):
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
            mcp_servers : Optional[List[Dict[str, Any]]], default None
                List of dicts, where each defines an MCP server/proxy:
                - For remote/SSE: {'type': 'sse', 'url': ..., 'auth_token': ...}
                - For local/stdio: {'type': 'stdio', 'script_path': 'server.py'}
                All discovered tools are available as functions to the agent.
            output_schema (Optional[Dict[str, Any]]): Schema for agent's output format.
            strict (bool): If True, always enforce output schema.

        Raises:
            ValueError: If the name is empty.
        """
        super().__init__(llm_config=llm_config)

        if not name:
            raise ValueError("Agent name cannot be empty")

        self.name = name
        self.workflow_id = workflow_id
        self.use_tools = use_tools
        self.tools = tools or []
        self.system_message = system_message
        self.keep_history = keep_history
        self.history_manager = None
        self.debugger = Debugger(name=self.name, workflow_id=None)
        self.debugger.start_session()
        self.chat_history: List[Dict[str, str]] = []
        self.mcp_servers = mcp_servers or []
        self._mcp_tool_names = set()
        self.output_schema = output_schema
        self.strict = strict

        if system_message:
            self.set_system_message(system_message)
        
        asyncio.run(self._load_mcp_tools())

    def set_workflow_id(self, workflow_id: str) -> None:
        """
        Set the workflow ID and initialize the history manager.
        This method is called by the Supervisor when registering the agent.

        Args:
            workflow_id (str): The workflow ID to set.
        """
        self.workflow_id = workflow_id
        self.debugger.update_workflow_id(workflow_id)
        self.history_manager = HistoryManager(workflow_id)
        
        if self.system_message and not self.history_manager.has_system_message(self.name):
            self.history_manager.append_message(
                message={"role": "system", "content": self.system_message},
                sender_type=EntityType.AGENT,
                sender_name=self.name
            )

    def set_system_message(self, message: str) -> None:
        """
        Set the system message for the agent, including output schema if specified.

        Args:
            message (str): The system message to set.
        """
        if self.output_schema:
            schema_instruction = (
                "\n\nYOU MUST ALWAYS RESPOND IN THE FOLLOWING FORMAT:\n"
                f"{json.dumps(self.output_schema, indent=2)}\n"
                "Your entire response must be valid JSON matching this schema.\n"
            )
            message = message + schema_instruction
        
        self.system_message = message
        self._reset_chat_history()

    def _validate_and_format_response(self, response: str) -> str:
        """
        Validate response against schema and reformat if needed.
        
        Args:
            response (str): Raw response from LLM
            
        Returns:
            str: Validated/formatted response
        """
        if not self.output_schema:
            return response

        try:
            parsed = json.loads(response)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            if not self.strict:
                return response
            
            format_prompt = (
                f"Given this response:\n'''\n{response}\n'''\n"
                f"Reformat it to match this schema:\n{json.dumps(self.output_schema, indent=2)}\n"
                "Return ONLY the formatted JSON, nothing else."
            )
            
            formatted = self.generate_response(
                messages=[{"role": "user", "content": format_prompt}]
            ).choices[0].message.content

            try:
                return json.dumps(json.loads(formatted))
            except json.JSONDecodeError:
                self.debugger.log("Schema enforcement failed", level="error")
                return response

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
                    tools=[tool['metadata'] for tool in self.tools],
                    use_tools=self.use_tools
                ).choices[0]

                if not response.finish_reason == "tool_calls":
                    user_query_answer = response.message.content
                    user_query_answer = self._validate_and_format_response(user_query_answer)
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
    
    async def _load_mcp_tools(self):
        """
        Discover and register tools from all MCP servers configured in self.mcp_servers.

        This method connects to each specified MCP server using the configured transport
        (either "sse" or "stdio"), retrieves the available tools, converts their schemas
        to OpenAI-compatible format, and registers proxy functions for each tool. It
        removes any previously loaded MCP tools before loading new ones.

        Raises:
            ValueError: If an unknown transport type is encountered in the MCP server config.
            Exception: For any network, process, or protocol-level error during tool discovery.
        """
        self._remove_all_mcp_tools()
        self._mcp_tool_names = set()
        for server in self.mcp_servers:
            ttype = server.get("type", "sse")  # default to sse
            try:
                if ttype == "sse":
                    url = server["url"]
                    auth_token = server.get("auth_token")
                    endpoint = url  # Use the user-supplied URL exactly as written
                    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                    async with sse_client(endpoint, headers=headers) as streams:
                        async with ClientSession(*streams) as session:
                            await session.initialize()
                            ntools_resp = await session.list_tools()
                            ntools = ntools_resp.tools
                            for tool in ntools:
                                openai_tool_meta = self._convert_mcp_tool_to_openai(tool)
                                tname = openai_tool_meta["function"]["name"]
                                proxy = self._build_mcp_tool_proxy(
                                    transport_type="sse",
                                    conf={"url": url, "auth_token": auth_token},
                                    tool_name=tname
                                )
                                tool_dict = {
                                    "tool": proxy,
                                    "metadata": openai_tool_meta,
                                    "_mcp_tool": True
                                }
                                self.tools.append(tool_dict)
                                self._mcp_tool_names.add(tname)
                elif ttype == "stdio":
                    script_path = server["script_path"]
                    server_params = StdioServerParameters(
                        command="python",
                        args=[script_path],
                        env=None
                    )
                    async with stdio_client(server_params) as (stdio, write):
                        async with ClientSession(stdio, write) as session:
                            await session.initialize()
                            ntools_resp = await session.list_tools()
                            ntools = ntools_resp.tools
                            for tool in ntools:
                                openai_tool_meta = self._convert_mcp_tool_to_openai(tool)
                                tname = openai_tool_meta["function"]["name"]
                                proxy = self._build_mcp_tool_proxy(
                                    transport_type="stdio",
                                    conf={"script_path": script_path},
                                    tool_name=tname
                                )
                                tool_dict = {
                                    "tool": proxy,
                                    "metadata": openai_tool_meta,
                                    "_mcp_tool": True
                                }
                                self.tools.append(tool_dict)
                                self._mcp_tool_names.add(tname)
                else:
                    raise ValueError(f"[MCP] Unknown transport type: {ttype}")
            except Exception as e:
                print(f"[MCP] Error loading tools from {server}: {e}")
        self.tools_metadata = [tool['metadata'] for tool in self.tools]

    def _convert_mcp_tool_to_openai(self, tool) -> Dict[str, Any]:
        """
        Convert an MCP tool object to an OpenAI-compatible function/tool schema.

        This method translates the MCP tool's name, description, and input schema
        into the OpenAI function calling format for inclusion in the agent's tool list.

        Args:
            tool: The MCP tool object as returned by the MCP server.

        Returns:
            Dict[str, Any]: The tool schema in OpenAI format, ready for tool calling.

        Note:
            - All input parameters will be set as required for compatibility with OpenAI.
        """
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": getattr(tool, 'description', '') or "MCP tool.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        # Extract properties and required fields from MCP input schema
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            property_names = []
            properties = schema.get("properties", {})
            for prop_name, prop_details in properties.items():
                prop_copy = {k: v for k, v in prop_details.items() if k != 'default'}
                openai_tool["function"]["parameters"]["properties"][prop_name] = prop_copy
                property_names.append(prop_name)
            openai_tool["function"]["parameters"]["required"] = property_names
        return openai_tool
            
    def _build_mcp_tool_proxy(self, transport_type, conf, tool_name):
        """
        Create a synchronous Python proxy function for invoking an MCP tool.

        Depending on the transport type ("sse" or "stdio"), this factory builds a proxy
        function that accepts tool arguments as keyword arguments, then manages the
        necessary asynchronous communication to invoke the MCP tool and retrieve the result.

        Args:
            transport_type (str): The MCP transport type ("sse" or "stdio").
            conf (dict): Connection configuration dictionary (e.g., URL or script_path).
            tool_name (str): Name of the tool to invoke on the MCP server.

        Returns:
            Callable: A Python function that accepts keyword arguments and returns the tool's result.

        Raises:
            Exception: If calling the MCP tool fails for transport or invocation reasons.
        """
        def proxy(**kwargs):
            async def _call_sse():
                url = conf["url"]
                auth_token = conf.get("auth_token")
                endpoint = url  # Use the user-supplied URL exactly as written
                headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
                async with sse_client(endpoint, headers=headers) as streams:
                    async with ClientSession(*streams) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=kwargs)
                        if hasattr(result, "content") and result.content:
                            return result.content[0].text
                        return str(result)
            async def _call_stdio():
                script_path = conf["script_path"]
                server_params = StdioServerParameters(
                    command="python",
                    args=[script_path],
                    env=None
                )
                async with stdio_client(server_params) as (stdio, write):
                    async with ClientSession(stdio, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=kwargs)
                        if hasattr(result, "content") and result.content:
                            return result.content[0].text
                        return str(result)
            try:
                if transport_type == "sse":
                    return asyncio.run(_call_sse())
                elif transport_type == "stdio":
                    return asyncio.run(_call_stdio())
                else:
                    raise ValueError(f"Unknown MCP transport {transport_type}")
            except Exception as e:
                return f"[MCP] Tool '{tool_name}' call failed: {e}"
        return proxy

    def _remove_all_mcp_tools(self):
        """
        Removes all tools loaded from MCP servers from self.tools.
        """
        self.tools = [t for t in self.tools if not t.get('_mcp_tool', False)]
        self._mcp_tool_names = set()
        
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get the current chat history.

        Returns:
            List[Dict[str, str]]: The current chat history.
        """
        return self.chat_history
    
    def update_mcp_tools(self):
        """
        Refresh the agent's tools by re-discovering available tools from all MCP servers.

        This method removes all previously registered MCP tools, re-connects to all configured
        MCP servers, and loads the updated tool lists into the agent. Call this method if you
        add, remove, or update tools on any MCP server during runtime.

        Raises:
            Exception: For any underlying error in the discovery or registration process.
        """
        asyncio.run(self._load_mcp_tools())
        
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
