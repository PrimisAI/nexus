"""
AgentFactory module for creating hierarchical structures of Supervisors and Agents.

This module provides a factory class that constructs a complete hierarchy of
Supervisors and Agents based on a configuration dictionary, typically loaded
from a YAML file.
"""

import importlib
from typing import Dict, Any, List
from primisai.nexus.core import Supervisor, Agent
from .config_validator import ConfigValidator

class AgentFactory:
    """
    A factory class for creating hierarchical structures of Supervisors and Agents.

    This class provides static methods to create a complete hierarchy of
    Supervisors and Agents based on a configuration dictionary. It handles
    the creation of tools for Agents and ensures proper nesting of
    Supervisors and Agents.
    """

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Supervisor:
        """
        Create a Supervisor with its entire hierarchy from a configuration dictionary.

        Args:
            config (Dict[str, Any]): The configuration dictionary containing
                the entire hierarchy structure.

        Returns:
            Supervisor: The root Supervisor of the created hierarchy.

        Raises:
            ConfigValidationError: If the configuration is invalid.
        """
        ConfigValidator.validate(config)
        return AgentFactory._create_supervisor(config['supervisor'], is_root=True)

    @staticmethod
    def _create_supervisor(supervisor_config: Dict[str, Any], is_root: bool = False) -> Supervisor:
        """
        Create a Supervisor instance and its children from a configuration dictionary.

        Args:
            supervisor_config (Dict[str, Any]): The configuration for this Supervisor.
            is_root (bool): Whether this Supervisor is the root of the hierarchy.

        Returns:
            Supervisor: The created Supervisor instance with all its children.
        """
        supervisor = Supervisor(
            name=supervisor_config['name'],
            llm_config=supervisor_config['llm_config'],
            system_message=supervisor_config['system_message']
        )

        for child_config in supervisor_config.get('children', []):
            if child_config['type'] == 'supervisor':
                child = AgentFactory._create_supervisor(child_config)
            else:  # agent
                child = AgentFactory._create_agent(child_config)
            supervisor.register_agent(child)

        return supervisor

    @staticmethod
    def _create_agent(agent_config: Dict[str, Any]) -> Agent:
        """
        Create an Agent instance from a configuration dictionary.

        Args:
            agent_config (Dict[str, Any]): The configuration for this Agent.

        Returns:
            Agent: The created Agent instance with its tools.
        """
        tools = AgentFactory._create_tools(agent_config.get('tools', []))
        return Agent(
            name=agent_config['name'],
            llm_config=agent_config['llm_config'],
            system_message=agent_config['system_message'],
            tools=tools,
            use_tools=bool(tools)
        )

    @staticmethod
    def _create_tools(tools_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a list of tool configurations from the provided tool configs.

        Args:
            tools_config (List[Dict[str, Any]]): List of tool configurations.

        Returns:
            List[Dict[str, Any]]: List of created tool configurations.
        """
        tools = []
        for tool_config in tools_config:
            tool_function = AgentFactory._import_function(tool_config['python_path'])
            metadata = {
                "type": "function",
                "function": {
                    "name": tool_config['name'],
                    "description": tool_config.get('description', ''),
                    "parameters": {
                        "type": "object",
                        "properties": tool_config.get('parameters', {}),
                        "required": list(tool_config.get('parameters', {}).keys())
                    }
                }
            }
            tools.append({"tool": tool_function, "metadata": metadata})
        return tools

    @staticmethod
    def _import_function(python_path: str):
        """
        Import a function from a given Python path.

        Args:
            python_path (str): The full path to the function, including module.

        Returns:
            Callable: The imported function.

        Raises:
            ImportError: If the module or function cannot be imported.
            AttributeError: If the specified function is not found in the module.
        """
        module_name, function_name = python_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, function_name)