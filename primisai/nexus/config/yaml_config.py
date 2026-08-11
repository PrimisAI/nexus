"""
YAML configuration loader module.

This module provides functions for loading YAML configuration files
and expanding environment variables within the configuration.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml

# Only expand ${VAR_NAME} syntax (not bare $VAR_NAME) in YAML config values.
# Using a regex that matches ${UPPER_OR_LOWER_OR_DIGITS_OR_UNDERSCORE} at word boundaries.
# Unset variables are left as the literal ${...} string (matching os.path.expandvars behavior).
_ENV_BRACED_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _expand_braced_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} occurrences with os.environ[VAR_NAME]; skip $BARE vars.

    Unlike ``os.path.expandvars``, bare ``$FOO`` references (without braces) are
    returned untouched, so unrelated $-prefixed tokens in YAML strings are not
    accidentally expanded. Missing env vars are left as the literal ``${NAME}``
    string, matching ``os.path.expandvars`` semantics.
    """
    def _repl(match: "re.Match[str]") -> str:
        name = match.group(1)
        if name in os.environ:
            return os.environ[name]
        return match.group(0)
    return _ENV_BRACED_RE.sub(_repl, value)


def load_yaml_config(file_path: str) -> dict[str, Any]:
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
        with open(file_path) as file:
            config = yaml.safe_load(file)
        return expand_env_vars(config)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")
    except OSError as e:
        raise OSError(f"Error reading configuration file: {e}")

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
        - Environment variables are expanded ONLY when written with the ``${VAR_NAME}``
          syntax. Bare ``$VAR_NAME`` references are left untouched to avoid accidentally
          expanding unrelated dollar-prefixed tokens in YAML strings.
        - If an environment variable is not set, it will be left unexpanded.
        - Non-string types are returned as-is.
    """
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(i) for i in config]
    elif isinstance(config, str):
        return _expand_braced_env_vars(config)
    return config