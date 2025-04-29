"""
ConfigValidator module for validating the configuration of Supervisors and Agents.

This module provides a ConfigValidator class that performs thorough validation
of the configuration dictionary used to create hierarchical structures of
Supervisors and Agents.
"""

from typing import Dict, Any, List

class ConfigValidationError(Exception):
    """
    Custom exception for configuration validation errors.

    This exception is raised when the configuration fails to meet
    the required structure or contains invalid data.
    """
    pass

class ConfigValidator:
    """
    A validator class for checking the structure and content of configuration dictionaries.

    This class provides static methods to validate the entire configuration
    hierarchy, including Supervisors, Agents, LLM configurations, and tools.
    """

    @staticmethod
    def validate(config: Dict[str, Any]) -> None:
        """
        Validate the entire configuration dictionary.

        Args:
            config (Dict[str, Any]): The configuration dictionary to validate.

        Raises:
            ConfigValidationError: If the configuration is invalid.
        """
        ConfigValidator._validate_supervisor(config.get('supervisor', {}), is_root=True)

    @staticmethod
    def _validate_supervisor(supervisor: Dict[str, Any], is_root: bool = False) -> None:
        """
        Validate a supervisor configuration.

        Args:
            supervisor (Dict[str, Any]): The supervisor configuration to validate.
            is_root (bool): Whether this supervisor is the root of the hierarchy.

        Raises:
            ConfigValidationError: If the supervisor configuration is invalid.
        """
        required_fields = ['name', 'type', 'llm_config', 'system_message']
        if is_root:
            required_fields.append('children')

        for field in required_fields:
            if field not in supervisor:
                raise ConfigValidationError(f"Missing required field '{field}' in supervisor configuration")

        if supervisor['type'] != 'supervisor':
            raise ConfigValidationError(f"Invalid type for supervisor: {supervisor['type']}")
        
        if 'is_assistant' in supervisor and not isinstance(supervisor['is_assistant'], bool):
            raise ConfigValidationError("'is_assistant' must be a boolean value")

        if is_root and supervisor.get('is_assistant', False):
            raise ConfigValidationError("Root supervisor cannot be an assistant supervisor")

        ConfigValidator._validate_llm_config(supervisor['llm_config'])

        for child in supervisor.get('children', []):
            if child['type'] == 'supervisor':
                if not child.get('is_assistant', False):
                    raise ConfigValidationError("Child supervisors must be assistant supervisors")
                ConfigValidator._validate_supervisor(child)
            elif child['type'] == 'agent':
                ConfigValidator._validate_agent(child)
            else:
                raise ConfigValidationError(f"Invalid type for child: {child['type']}")

    @staticmethod
    def _validate_agent(agent: Dict[str, Any]) -> None:
        """
        Validate an agent configuration.

        Args:
            agent (Dict[str, Any]): The agent configuration to validate.

        Raises:
            ConfigValidationError: If the agent configuration is invalid.
        """
        required_fields = ['name', 'type', 'llm_config', 'system_message']
        for field in required_fields:
            if field not in agent:
                raise ConfigValidationError(f"Missing required field '{field}' in agent configuration")
                
        bool_fields = ['keep_history', 'use_tools', 'strict']
        for field in bool_fields:
            if field in agent and not isinstance(agent[field], bool):
                raise ConfigValidationError(f"'{field}' must be a boolean value")
                
        if 'output_schema' in agent:
            if not isinstance(agent['output_schema'], dict):
                raise ConfigValidationError("output_schema must be a dictionary")
            if 'type' not in agent['output_schema']:
                raise ConfigValidationError("output_schema must have 'type' field")
                
        if 'mcp_servers' in agent:
            if not isinstance(agent['mcp_servers'], list):
                raise ConfigValidationError("mcp_servers must be a list")
            for server in agent['mcp_servers']:
                if 'type' not in server:
                    raise ConfigValidationError("Each MCP server must have 'type' field")
                if server['type'] not in ['sse', 'stdio']:
                    raise ConfigValidationError("MCP server type must be 'sse' or 'stdio'")
                if server['type'] == 'sse' and 'url' not in server:
                    raise ConfigValidationError("SSE MCP server must have 'url' field")
                if server['type'] == 'stdio' and 'script_path' not in server:
                    raise ConfigValidationError("stdio MCP server must have 'script_path' field")
        
        ConfigValidator._validate_llm_config(agent['llm_config'])
        ConfigValidator._validate_tools(agent.get('tools', []))

    @staticmethod
    def _validate_llm_config(llm_config: Dict[str, Any]) -> None:
        """
        Validate the LLM (Language Model) configuration.

        Args:
            llm_config (Dict[str, Any]): The LLM configuration to validate.

        Raises:
            ConfigValidationError: If the LLM configuration is invalid.
        """
        required_fields = ['model', 'api_key', 'base_url']
        for field in required_fields:
            if field not in llm_config:
                raise ConfigValidationError(f"Missing required field '{field}' in llm_config")

    @staticmethod
    def _validate_tools(tools: List[Dict[str, Any]]) -> None:
        """
        Validate the list of tools in an agent's configuration.

        Args:
            tools (List[Dict[str, Any]]): The list of tool configurations to validate.

        Raises:
            ConfigValidationError: If any tool configuration is invalid.
        """
        for tool in tools:
            required_fields = ['name', 'type', 'python_path']
            for field in required_fields:
                if field not in tool:
                    raise ConfigValidationError(f"Missing required field '{field}' in tool configuration")

            if tool['type'] != 'function':
                raise ConfigValidationError(f"Invalid tool type: {tool['type']}")