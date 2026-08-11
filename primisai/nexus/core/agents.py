"""
Agent module for handling specialized AI interactions.

This module provides an Agent class that extends the base AI functionality
with additional features like tool usage and chat history management.
"""

import json, asyncio
import logging
import threading
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from openai.types.chat import ChatCompletionMessage
from primisai.nexus.core.ai import AI
from primisai.nexus.history import HistoryManager, EntityType
from primisai.nexus.utils import Debugger
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
logger = logging.getLogger(__name__)

# and any future v2 migration checklist can compare against them.
# _MCP_V1_IMPORTS_REQUIRED = (
#     ("mcp", ["ClientSession", "StdioServerParameters"]),
#     ("mcp.client.sse", ["sse_client"]),
#     ("mcp.client.stdio", ["stdio_client"]),
# )

try:
    from importlib.metadata import version as _mcp_pkg_version

    def _mcp_major_version() -> int:
        try:
            return int(_mcp_pkg_version("mcp").split(".", 1)[0])
        except Exception:
            return 1

    if _mcp_major_version() >= 2:
        raise ImportError(
            "primisai (Nexus) has not yet been migrated to the MCP SDK v2 API.\n"
            "  The following v1 imports must be ported BEFORE upgrading to mcp>=2:\n"
            "  Please pin `mcp[cli]>=1.10.0,<2.0.0` in the meantime, or see the\n"
        )
except Exception:
    pass

class Agent(AI):
    """
    An Agent class that extends the base AI functionality.

    This class handles specialized interactions, including the use of tools
    and management of chat history. It can operate independently or as part
    of a supervised workflow.
    """

    def __init__(self,
                 name: str,
                 llm_config: dict[str, str],
                 workflow_id: str | None = None,
                 tools: list[dict[str, Any]] | None = None,
                 system_message: str | None = None,
                 use_tools: bool = False,
                 keep_history: bool = True,
                 mcp_servers: list[dict[str, Any]] | None = None,
                 output_schema: dict[str, Any] | None = None,
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
        self.chat_history: list[dict[str, str]] = []
        self.mcp_servers = mcp_servers or []
        self._mcp_tool_names = set()
        self.output_schema = output_schema
        self.strict = strict
        self._mcp_sessions: Dict[str, Dict[str, Any]] = {}
        self._mcp_loop: asyncio.AbstractEventLoop | None = None
        self._mcp_loop_thread: threading.Thread | None = None
        self._mcp_loop_ready = threading.Event()

        

        if system_message:
            self.set_system_message(system_message)
            #asyncio.run(self._load_mcp_tools()) #Updated
        # Safe async initialization
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # Event loop already running (Jupyter/notebook/async app).
                # Block until tools are loaded by running asyncio.run in a
                # worker thread so we don't interfere with the existing loop.
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(asyncio.run, self._load_mcp_tools()).result()
            else:
                loop.run_until_complete(self._load_mcp_tools())
        except RuntimeError:
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

    def chat(self, query: str, sender_name: str | None = None) -> str:
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
                # Check if we actually have tools before enabling use_tools
                has_tools = bool(self.tools)
                
                response = self.generate_response(
                    self.chat_history,
                    tools=[tool['metadata'] for tool in self.tools] if has_tools else None,
                    use_tools=self.use_tools and has_tools
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
                
                all_tool_calls = response.message.tool_calls
                tool_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            'id': tc.id,
                            'type': 'function',
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        }
                        for tc in all_tool_calls
                    ]
                }
                self.chat_history.append(tool_msg)

                for tool_call in all_tool_calls:
                    tool_msg_id = None
                    if self.history_manager:
                        tool_msg_id = self.history_manager.append_message(
                            message=tool_msg,
                            sender_type=EntityType.AGENT,
                            sender_name=self.name,
                            parent_id=query_msg_id,
                            tool_call_id=tool_call.id
                        )

                    self._process_tool_call(tool_call, tool_msg_id)

            except Exception as e:
                error_msg = f"Error in chat processing: {str(e)}"
                self.debugger.log(error_msg)
                raise RuntimeError(error_msg)

    def _process_tool_call(self, tool_call, parent_msg_id: str | None = None) -> None:
        """
        Process a single tool call from the chat response.

        Args:
            tool_call: A single tool call object (from ChatCompletionMessage.tool_calls).
            parent_msg_id (Optional[str]): ID of the parent message in history.

        Raises:
            ValueError: If the specified tool is not found or if there's an error in processing arguments.
        """
        if tool_call is None:
            raise ValueError("Tool call is None")

        function_call = tool_call
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
            try:
                tool_feedback = tool_function(**tool_arguments)
            except TypeError:
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

    def _ensure_mcp_loop(self) -> asyncio.AbstractEventLoop:
        if self._mcp_loop is not None:
            return self._mcp_loop

        def _thread_main():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._mcp_loop = loop
            self._mcp_loop_ready.set()
            try:
                loop.run_forever()
            finally:
                loop.close()

        self._mcp_loop_thread = threading.Thread(target=_thread_main, daemon=True)
        self._mcp_loop_thread.start()
        self._mcp_loop_ready.wait()
        return self._mcp_loop

    def _run_in_mcp_loop(self, coro, timeout=None):
        loop = self._ensure_mcp_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    async def _a_close_all_mcp_sessions(self):
        for key, entry in list(self._mcp_sessions.items()):
            session = entry.get("session")
            streams = entry.get("streams")
            ttype = entry.get("type")
            try:
                if session is not None:
                    try:
                        await session.__aexit__(None, None, None)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if streams is not None:
                    if ttype == "stdio":
                        try:
                            await stdio_client.__aexit__(streams, None, None, None)
                        except Exception:
                            try:
                                stdio, write = streams
                                try:
                                    stdio.close()
                                except Exception:
                                    pass
                                try:
                                    write.close()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    else:
                        try:
                            await sse_client.__aexit__(streams, None, None, None)
                        except Exception:
                            try:
                                reader, writer = streams
                                try:
                                    writer.close()
                                    await writer.wait_closed()
                                except Exception:
                                    pass
                                try:
                                    reader.close()
                                except Exception:
                                    pass
                            except Exception:
                                pass
            except Exception:
                pass
        self._mcp_sessions.clear()

    async def _load_mcp_tools(self):
        """
        Discover and register tools from all MCP servers configured in self.mcp_servers.

        This method connects to each specified MCP server using the configured transport
        (either "sse" or "stdio"), retrieves the available tools, converts their schemas
        to OpenAI-compatible format, and registers proxy functions for each tool. It
        removes any previously loaded MCP tools before loading new ones. Sessions are
        kept open in a persistent cache so subsequent tool calls don't reconnect.

        Raises:
            ValueError: If an unknown transport type is encountered in the MCP server config.
            Exception: For any network, process, or protocol-level error during tool discovery.
        """
        await self._a_close_all_mcp_sessions()
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
                    streams = await sse_client(endpoint, headers=headers).__aenter__()
                    session = ClientSession(*streams)
                    await session.__aenter__()
                    try:
                        await session.initialize()
                        key = f"{ttype}:{url}::{auth_token or ''}"
                        self._mcp_sessions[key] = {"session": session, "streams": streams, "type": ttype}
                        ntools_resp = await session.list_tools()
                        ntools = ntools_resp.tools
                        for tool in ntools:
                            openai_tool_meta = self._convert_mcp_tool_to_openai(tool)
                            tname = openai_tool_meta["function"]["name"]
                            proxy = self._build_mcp_tool_proxy(
                                transport_type="sse",
                                conf={"url": url, "auth_token": auth_token, "_session_key": key},
                                tool_name=tname
                            )
                            tool_dict = {
                                "tool": proxy,
                                "metadata": openai_tool_meta,
                                "_mcp_tool": True
                            }
                            self.tools.append(tool_dict)
                            self._mcp_tool_names.add(tname)
                    except Exception:
                        try:
                            await session.__aexit__(None, None, None)
                        except Exception:
                            pass
                        try:
                            await sse_client.__aexit__(streams, None, None, None)
                        except Exception:
                            pass
                        raise
                elif ttype == "stdio":
                    script_path = server["script_path"]
                    server_params = StdioServerParameters(
                        command="python",
                        args=[script_path],
                        env=None
                    )
                    streams = await stdio_client(server_params).__aenter__()
                    stdio, write = streams
                    session = ClientSession(stdio, write)
                    await session.__aenter__()
                    try:
                        await session.initialize()
                        key = f"{ttype}:{script_path}"
                        self._mcp_sessions[key] = {"session": session, "streams": streams, "type": ttype}
                        ntools_resp = await session.list_tools()
                        ntools = ntools_resp.tools
                        for tool in ntools:
                            openai_tool_meta = self._convert_mcp_tool_to_openai(tool)
                            tname = openai_tool_meta["function"]["name"]
                            proxy = self._build_mcp_tool_proxy(
                                transport_type="stdio",
                                conf={"script_path": script_path, "_session_key": key},
                                tool_name=tname
                            )
                            tool_dict = {
                                "tool": proxy,
                                "metadata": openai_tool_meta,
                                "_mcp_tool": True
                            }
                            self.tools.append(tool_dict)
                            self._mcp_tool_names.add(tname)
                    except Exception:
                        try:
                            await session.__aexit__(None, None, None)
                        except Exception:
                            pass
                        try:
                            await stdio_client.__aexit__((stdio, write), None, None, None)
                        except Exception:
                            pass
                        raise
                else:
                    raise ValueError(f"[MCP] Unknown transport type: {ttype}")
            except Exception as e:
                logger.warning(f"[MCP] Error loading tools from {server}: {e}")
        self.tools_metadata = [tool['metadata'] for tool in self.tools]

    def _convert_mcp_tool_to_openai(self, tool) -> dict[str, Any]:
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
            properties = schema.get("properties", {})
            for prop_name, prop_details in properties.items():
                prop_copy = {k: v for k, v in prop_details.items() if k != 'default'}
                openai_tool["function"]["parameters"]["properties"][prop_name] = prop_copy
            if schema.get("required") is not None:
                openai_tool["function"]["parameters"]["required"] = list(schema["required"])
        return openai_tool
            
    def _build_mcp_tool_proxy(self, transport_type, conf, tool_name):
        """
        Create a synchronous Python proxy function for invoking an MCP tool.

        Uses a persistent session (kept alive in a background asyncio event loop
        on a dedicated thread) so repeated tool calls reuse the same transport
        and ClientSession rather than reconnecting + re-initializing each call.

        Args:
            transport_type (str): The MCP transport type ("sse" or "stdio").
            conf (dict): Connection configuration dictionary, carrying the
                `_session_key` used to look up the already-opened session.
            tool_name (str): Name of the tool to invoke on the MCP server.

        Returns:
            Callable: A Python function that accepts keyword arguments and
                returns the tool's result. Uses the persistent session stored
                under the `_session_key` in `self._mcp_sessions`.
        """
        session_key = conf.get("_session_key")

        def proxy(**kwargs):
            async def _call_with_session():
                entry = self._mcp_sessions.get(session_key)
                if entry is None:
                    raise RuntimeError(
                        f"[MCP] Persistent session for key {session_key!r} not available"
                    )
                session = entry["session"]
                result = await session.call_tool(tool_name, arguments=kwargs)
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                return str(result)
            try:
                return self._run_in_mcp_loop(_call_with_session())
            except Exception as e:
                return f"[MCP] Tool '{tool_name}' call failed: {e}"
        return proxy

    def _remove_all_mcp_tools(self):
        """
        Removes all tools loaded from MCP servers from self.tools.
        """
        self.tools = [t for t in self.tools if not t.get('_mcp_tool', False)]
        self._mcp_tool_names = set()
        
    def get_chat_history(self) -> list[dict[str, str]]:
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
        add, remove, or update tools on any MCP server during runtime. Runs on the persistent
        background MCP loop so sessions stay bound to the owning event loop.

        Raises:
            Exception: For any underlying error in the discovery or registration process.
        """
        if self._mcp_loop is not None:
            self._run_in_mcp_loop(self._load_mcp_tools())
        else:
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
