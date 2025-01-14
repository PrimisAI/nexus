"""
YAML configuration loader module.

This module provides functions for loading YAML configuration files
and expanding environment variables within the configuration.
"""

import os
import yaml
from typing import Dict, Any

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file and expand its environment variables.

    This function reads a YAML file, parses its contents, and then
    expands any environment variables found within the configuration.

    Args:
        file_path (str): The path to the YAML configuration file.

    Returns:
        Dict[str, Any]: The loaded and processed configuration as a dictionary.

    Raises:
        FileNotFoundError: If the specified file_path does not exist.
        yaml.YAMLError: If there's an error parsing the YAML file.
        IOError: If there's an error reading the file.
    """
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return expand_env_vars(config)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")
    except IOError as e:
        raise IOError(f"Error reading configuration file: {e}")

def expand_env_vars(config: Any) -> Any:
    """
    Recursively expand environment variables in a configuration.

    This function traverses through the configuration data structure
    (which can be a nested dictionary, list, or a string) and expands
    any environment variables it encounters.

    Args:
        config (Any): The configuration item to process. Can be a dict, list, str, or any other type.

    Returns:
        Any: The processed configuration item with expanded environment variables.

    Note:
        - Environment variables should be in the format ${VAR_NAME} or $VAR_NAME.
        - If an environment variable is not set, it will be left unexpanded.
        - Non-string types are returned as-is.
    """
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(i) for i in config]
    elif isinstance(config, str):
        return os.path.expandvars(config)
    return config