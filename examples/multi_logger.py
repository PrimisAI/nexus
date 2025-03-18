import os, sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

# Tool 1: Calculator
calculator_metadata = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform basic arithmetic operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "num1": {"type": "integer", "description": "First number"},
                "num2": {"type": "integer", "description": "Second number"},
                "operation": {
                    "type": "string",
                    "description": "Mathematical operation to perform",
                    "enum": ["add", "subtract", "multiply", "divide"]
                }
            },
            "required": ["num1", "num2", "operation"]
        }
    }
}

def calculator(num1: int, num2: int, operation: str) -> float:
    if operation == "add": return num1 + num2
    elif operation == "subtract": return num1 - num2
    elif operation == "multiply": return num1 * num2
    elif operation == "divide": return num1 / num2
    else: raise ValueError("Invalid operation")

# Tool 2: Text Processor
text_processor_metadata = {
    "type": "function",
    "function": {
        "name": "process_text",
        "description": "Process text with various operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to process"},
                "operation": {
                    "type": "string",
                    "description": "Text operation to perform",
                    "enum": ["uppercase", "lowercase", "reverse"]
                }
            },
            "required": ["text", "operation"]
        }
    }
}

def text_processor(text: str, operation: str) -> str:
    if operation == "uppercase": return text.upper()
    elif operation == "lowercase": return text.lower()
    elif operation == "reverse": return text[::-1]
    else: raise ValueError("Invalid operation")

def create_supervisor():

    # Create agents with their respective tools
    calculator_agent = Agent(
        name="Calculator_Agent",
        llm_config=llm_config,
        system_message="You are a mathematical calculator agent.",
        tools=[{"tool": calculator, "metadata": calculator_metadata}],
        use_tools=True
    )

    text_agent = Agent(
        name="Text_Processor_Agent",
        llm_config=llm_config,
        system_message="You are a text processing agent.",
        tools=[{"tool": text_processor, "metadata": text_processor_metadata}],
        use_tools=True
    )

    # Create supervisor
    supervisor = Supervisor(
        name="Multi_Tool_Supervisor",
        llm_config=llm_config,
        system_message="""You are a helpful supervisor who can assign tasks to agents."""
    )

    # Register agents with supervisor
    supervisor.register_agent(calculator_agent)
    supervisor.register_agent(text_agent)

    return supervisor


if __name__ == "__main__":
    
    for i in range(1, 3):
        # Use this example query:  I need three things done: 1. Add 15 and 27 2. Convert 'Hello World' to uppercase 3. Multiply 8 by 6
        supervisor = create_supervisor()
        supervisor.start_interactive_session()


