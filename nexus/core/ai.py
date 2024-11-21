import openai
from typing import List, Dict


class AI:
    def __init__(self, llm_config: Dict[str, str]):

        self.llm_config = llm_config
        self.client = openai.OpenAI(base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                                    api_key=llm_config['api_key'])

    def generate_response(self, messages: List[Dict[str, str]], tools: list, use_tools: bool = False) -> Dict:
        """
        Execute a chat completion.

        Args:
            messages (List[Dict[str, str]]): List of conversation messages.
            use_tools (bool): Whether to use function calling with tools.

        Returns:
            Dict: The response from the OpenAI API.
        """

        try:
            params = {
                "model": self.llm_config['model'],
                "messages": messages,
                "temperature": float(self.llm_config.get('temperature', 0.7))
            }

            if use_tools and tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            return {"error": f"Chat failed: {str(e)}"}
