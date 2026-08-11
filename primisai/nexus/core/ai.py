"""
AI module for handling interactions with OpenAI's API.

This module provides a base AI class for generating responses using OpenAI's chat completions.
"""

import openai 
from typing import Any
from openai.types.chat import ChatCompletion 

# OpenAI SDK v2 detection helper (used ONLY if the upper bound pin is lifted).
# guard so the moment someone tries `openai>=2` they get a helpful ImportError
# rather than silent breakage.
try:
    from importlib.metadata import version as _pkg_version

    def _openai_major_version() -> int:
        try:
            return int(_pkg_version("openai").split(".", 1)[0])
        except Exception:
            return 1

    if _openai_major_version() >= 2:
        raise ImportError(
            "primisai (Nexus) has not yet been migrated to the openai SDK v2 API.\n"
            "Please pin `openai>=1.66.3,<2.0.0` or check the migration notes in\n"
            "primisai/nexus/core/ai.py before upgrading to openai>=2."
        )
except Exception:
    pass


class AI:
    """
    A base class for AI interactions using OpenAI's API.

    This class handles the configuration and execution of chat completions,
    including optional function calling with tools.
    """

    def __init__(self, llm_config: dict[str, str]):
        """
        Initialize the AI instance.

        Args:
            llm_config (Dict[str, str]): Configuration for the language model.
                Must contain 'api_key' and 'model'. May optionally include 'base_url' and 'temperature'.

        Raises:
            ValueError: If required configuration keys are missing or if tools are enabled but not provided.
        """
        if not all(key in llm_config for key in ['api_key', 'model']):
            raise ValueError("llm_config must contain 'api_key' and 'model'")

        self.llm_config = llm_config
        self.client = openai.OpenAI(
            base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
            api_key=llm_config['api_key']
        )

    def generate_response(self,
                          messages: list[dict[str, str]],
                          tools: list[dict[str, Any]] | None = None,
                          use_tools: bool = False) -> ChatCompletion:
        """
        Execute a chat completion.

        Args:
            messages (List[Dict[str, str]]): List of conversation messages.
            tools (Optional[List[Dict[str, Any]]]): List of tools for function calling.
            use_tools (bool): Whether to use function calling with tools.

        Returns:
            ChatCompletion: The response from the OpenAI API.

        Raises:
            openai.OpenAIError: If there's an error in the API call.
            ValueError: If tools are requested but not provided.
        """
        if use_tools and not tools:
            raise ValueError("Tools must be provided when use_tools is True")

        try:
            params = self.llm_config.copy()

            params.pop('api_key', None)
            params.pop('base_url', None)

            params['messages'] = messages

            if use_tools:
                params['tools'] = tools
                params['tool_choice'] = 'auto'

            return self.client.chat.completions.create(**params)

        except openai.OpenAIError as e:
            raise openai.OpenAIError(f"Chat completion failed: {str(e)}")

    def __str__(self) -> str:
        """Return a string representation of the AI instance."""
        return f"AI(model={self.llm_config['model']})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the AI instance."""
        return f"AI(llm_config={self.llm_config})"
