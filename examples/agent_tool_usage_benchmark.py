import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor

# Load environment variables for LLM credentials
load_dotenv()

llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

# === Define Two Tools for a "MathAgent" ===
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

math_tools = [
    {
        "tool": add,
        "metadata": {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            }
        }
    },
    {
        "tool": multiply,
        "metadata": {
            "type": "function",
            "function": {
                "name": "multiply",
                "description": "Multiply two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            }
        }
    }
]

math_agent = Agent(
    name="MathAgent",
    llm_config=llm_config,
    system_message="You are an agent skilled at performing arithmetic calculations like addition and multiplication. "
                  "When asked to calculate values, use your tools. If a question involves multiple calculations, use all tools as needed."
                  "You should use Agents and tools in parallel if possible.",
    tools=math_tools,
    use_tools=True
)

# === Define Agent 2: TextAgent with two tools: upper and reverse ===
def to_uppercase(text: str) -> str:
    return text.upper()

def reverse_text(text: str) -> str:
    return text[::-1]

text_tools = [
    {
        "tool": to_uppercase,
        "metadata": {
            "type": "function",
            "function": {
                "name": "to_uppercase",
                "description": "Convert text to uppercase.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert"}
                    },
                    "required": ["text"]
                }
            }
        }
    },
    {
        "tool": reverse_text,
        "metadata": {
            "type": "function",
            "function": {
                "name": "reverse_text",
                "description": "Reverse the given text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to reverse"}
                    },
                    "required": ["text"]
                }
            }
        }
    }
]

text_agent = Agent(
    name="TextAgent",
    llm_config=llm_config,
    system_message="You are a helpful text processing agent, skilled in text transformation tasks like uppercase conversion and text reversal.",
    tools=text_tools,
    use_tools=True
)

# === Supervisor Setup ===
supervisor = Supervisor(
    name="SuperSupervisor",
    llm_config=llm_config,
    system_message="You are a manager who delegates math and text tasks to the appropriate agents. For user requests involving both math and text, delegate each part to the correct agent so all results are collected in one answer."
)
supervisor.register_agent(math_agent)
supervisor.register_agent(text_agent)

supervisor.display_agent_graph()

if __name__ == "__main__":
    print("\nDemo: Multi-Agent, Multi-Tool in One Turn\n")
    complex_query = (
        "Please do all of the following:"
        "\n1. Add 7 and 3, and multiply 4 and 6."
        "\n2. Convert 'hello world' to uppercase and also reverse 'chatbot'."
    )
    print(f"User: {complex_query}\n")

    response = supervisor.chat(complex_query)
    print(f"\nSuperSupervisor: {response}")
    print("\nYou just witnessed a response where Supervisor delegated to both agents, and MathAgent performed two tool calls in one reply (add & multiply), and TextAgent likewise (uppercase & reverse).")