import sys, os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent

load_dotenv()

llm_config = {'model': os.getenv('LLM_MODEL'), 'api_key': os.getenv('LLM_API_KEY'), 'base_url': os.getenv('LLM_BASE_URL')}

test_tool_metadata = {
    "type": "function",
    "function": {
        "name": "test_tool",
        "description": (
            "Simple sum test function."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "num1": {
                    "type": "integer",
                    "description": (
                        "first integer"
                    )
                },
                "num2": {
                    "type": "integer",
                    "description": (
                        "second integer"
                    )
                },
                "num3": {
                    "type": "integer",
                    "description": (
                        "third integer"
                    )
                }                  
            },
            "required": ["num1", "num2", "num3"]
        }
    }
}

def test_tool_func(num1: int, num2: int, num3: int):
    return num1 + num2 - num3

test_tool = [{"tool": test_tool_func, "metadata": test_tool_metadata}]

test_agent = Agent(
    name="Test Agent",
    system_message=f"You are the Test Agent.",
    llm_config=llm_config,
    tools=test_tool,
    use_tools=True)

response = test_agent.chat("Can you run test tool with input value 4, 6 and 5?")