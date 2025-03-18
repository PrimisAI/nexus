"""
Example demonstrating comprehensive usage of the history management system
with various scenarios and detailed history viewing.
"""

import os, sys
from dotenv import load_dotenv
from typing import Dict, Any, List, Union

# Assuming primisai is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor
from openai.types.chat import ChatCompletionMessage


# Load environment variables
load_dotenv()

def message_to_dict(msg: Union[Dict[str, Any], ChatCompletionMessage]) -> Dict[str, Any]:
    """Convert a message to dictionary format regardless of its type."""
    if isinstance(msg, dict):
        return msg
    elif isinstance(msg, ChatCompletionMessage):
        message_dict = {'role': msg.role, 'content': msg.content}
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            message_dict['tool_calls'] = [
                {
                    'id': tool_call.id,
                    'function': {
                        'name': tool_call.function.name,
                        'arguments': tool_call.function.arguments
                    }
                }
                for tool_call in msg.tool_calls
            ]
        return message_dict
    else:
        raise ValueError(f"Unsupported message type: {type(msg)}")

def print_formatted_history(title: str, messages: List[Union[Dict[str, Any], ChatCompletionMessage]]) -> None:
    """Pretty print message history with clear formatting."""
    print("\n" + "="*50)
    print(f"{title}")
    print("="*50)
    
    for msg in messages:
        print("\n---Message---")
        msg_dict = message_to_dict(msg)
        
        print(f"Role: {msg_dict['role']}")
        
        # Format content based on message type
        if msg_dict['role'] == 'assistant' and 'tool_calls' in msg_dict:
            print("Content:", msg_dict['content'])
            print("Tool Calls:")
            for tool_call in msg_dict['tool_calls']:
                print(f"  - Function: {tool_call['function']['name']}")
                print(f"    Arguments: {tool_call['function']['arguments']}")
        elif msg_dict['role'] == 'tool':
            print(f"Content: {msg_dict['content']}")
            if 'tool_call_id' in msg_dict:
                print(f"Tool Call ID: {msg_dict['tool_call_id']}")
        else:
            print(f"Content: {msg_dict['content']}")
    print("\n" + "="*50 + "\n")

def main():
    # Configuration
    llm_config = {
        'model': os.getenv('LLM_MODEL'),
        'api_key': os.getenv('LLM_API_KEY'),
        'base_url': os.getenv('LLM_BASE_URL')
    }

    # Create supervisor and agents
    supervisor = Supervisor(
        name="MainSupervisor",
        llm_config=llm_config,
        system_message="You are a helpful supervisor coordinating multiple agents."
    )

    # Create specialized agents
    math_agent = Agent(
        name="MathAgent",
        llm_config=llm_config,
        system_message="You are a mathematical computation specialist."
    )

    writing_agent = Agent(
        name="WritingAgent",
        llm_config=llm_config,
        system_message="You are a creative writing specialist."
    )

    # Register agents
    supervisor.register_agent(math_agent)
    supervisor.register_agent(writing_agent)

    # Scenario 1: Direct supervisor response
    print("\nScenario 1: Direct supervisor response")
    query = "What's your name?"
    response = supervisor.chat(query)
    print(f"User: {query}")
    print(f"Supervisor: {response}")
    print_formatted_history("Supervisor Direct Response History", supervisor.get_chat_history())

    # Scenario 2: Single agent delegation
    print("\nScenario 2: Single agent delegation")
    query = "Calculate 15 + 27"
    response = supervisor.chat(query)
    print(f"User: {query}")
    print(f"Final Response: {response}")
    print_formatted_history("Supervisor History with Agent Delegation", supervisor.get_chat_history())
    print_formatted_history("Math Agent History", math_agent.get_chat_history())

    # Scenario 3: Multiple agent interaction
    print("\nScenario 3: Multiple agent interaction")
    query = """I need two things:
    1. Calculate 25 * 4
    2. Write a haiku about mathematics"""
    response = supervisor.chat(query)
    print(f"User: {query}")
    print(f"Final Response: {response}")
    
    print("\nFull conversation history after multiple interactions:")
    print("\nSupervisor History:")
    print_formatted_history("Complete Supervisor History", supervisor.get_chat_history())
    
    print("\nMath Agent History:")
    print_formatted_history("Math Agent History", math_agent.get_chat_history())
    
    print("\nWriting Agent History:")
    print_formatted_history("Writing Agent History", writing_agent.get_chat_history())

    # Scenario 4: Agent with tools
    calculator_metadata = {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic arithmetic",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                    "numbers": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["operation", "numbers"]
            }
        }
    }

    def calculator(operation: str, numbers: List[float]) -> float:
        if operation == "add":
            return sum(numbers)
        elif operation == "multiply":
            result = 1
            for num in numbers:
                result *= num
            return result
        raise ValueError(f"Unsupported operation: {operation}")

    # Create new agent with tool
    calc_agent = Agent(
        name="CalculatorAgent",
        llm_config=llm_config,
        system_message="You are a calculator agent with built-in computation tools.",
        tools=[{"tool": calculator, "metadata": calculator_metadata}],
        use_tools=True
    )
    supervisor.register_agent(calc_agent)

    query = "Calculate the product of 5, 3, and 4"
    response = supervisor.chat(query)
    print(f"\nScenario 4: Tool-enabled agent")
    print(f"User: {query}")
    print(f"Final Response: {response}")
    
    print("\nSupervisor History with Tool-enabled Agent:")
    print_formatted_history("Supervisor History", supervisor.get_chat_history())
    
    print("\nCalculator Agent History:")
    print_formatted_history("Calculator Agent History", calc_agent.get_chat_history())
    
    
    query = "How many agents you have? tell name of every agent."
    response = supervisor.chat(query)
    print(f"\nScenario 5: Tool-enabled agent")
    print(f"User: {query}")
    print(f"Final Response: {response}")

if __name__ == "__main__":
    main()