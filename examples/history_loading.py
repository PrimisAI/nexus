import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primisai.nexus.core import Agent, Supervisor
from primisai.nexus.history import HistoryManager

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

def create_calculator_agent():
    """Create a calculator agent with tools."""
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

    return Agent(
        name="Calculator_Agent",
        llm_config=llm_config,
        system_message="You are a mathematical calculator agent.",
        tools=[{"tool": calculator, "metadata": calculator_metadata}],
        use_tools=True
    )

def create_text_agent():
    """Create a text processing agent with tools."""
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

    return Agent(
        name="Text_Processor_Agent",
        llm_config=llm_config,
        system_message="You are a text processing agent.",
        tools=[{"tool": text_processor, "metadata": text_processor_metadata}],
        use_tools=True
    )

def test_history_management():
    """Test history management functionality."""
    print("\n=== Testing History Management ===\n")

    # Create a new supervisor and agents
    supervisor = Supervisor(
        name="History_Test_Supervisor",
        llm_config=llm_config,
        system_message="You are a supervisor managing calculation and text processing tasks."
    )

    calc_agent = create_calculator_agent()
    text_agent = create_text_agent()

    supervisor.register_agent(calc_agent)
    supervisor.register_agent(text_agent)
    
    # supervisor.display_agent_graph()

    # Display initial structure
    print("Initial Agent Structure:")
    supervisor.display_agent_graph()
    print("\n")

    # Test 1: Initial interaction
    print("Test 1: Initial interaction")
    query = "Add 15 and 27, then convert 'Hello World' to uppercase"
    print(f"Query: {query}")
    response = supervisor.chat(query)
    print(f"Response: {response}\n")

    # Store workflow_id for later use
    workflow_id = supervisor.workflow_id

    # Test 2: Create new supervisor with same workflow_id and load history
    print("Test 2: Loading history into new supervisor instance")
    new_supervisor = Supervisor(
        name="History_Test_Supervisor",
        llm_config=llm_config,
        system_message="You are a supervisor managing calculation and text processing tasks.",
        workflow_id=workflow_id
    )

    # Initialize history manager
    history_manager = HistoryManager(workflow_id)

    # Create new agents
    new_calc_agent = create_calculator_agent()
    new_text_agent = create_text_agent()

    # Register agents
    new_supervisor.register_agent(new_calc_agent)
    new_supervisor.register_agent(new_text_agent)

    # Load histories
    new_supervisor.chat_history = history_manager.load_chat_history("History_Test_Supervisor")
    new_calc_agent.chat_history = history_manager.load_chat_history("Calculator_Agent")
    new_text_agent.chat_history = history_manager.load_chat_history("Text_Processor_Agent")
    
    print("History_Test_Supervisor: \n", new_supervisor.chat_history)
    print("\nCalculator_Agent: \n", new_calc_agent.chat_history)
    print("\nText_Processor_Agent: \n", new_text_agent.chat_history)

    # Display loaded histories
    print("\nLoaded Chat Histories:")
    
    print("\nSupervisor History:")
    for msg in new_supervisor.chat_history:
        print(f"Role: {msg['role']}, "
              f"Content: {msg.get('content', 'None')}, "
              f"Tool Calls: {'Yes' if 'tool_calls' in msg else 'No'}")

    print("\nCalculator Agent History:")
    for msg in new_calc_agent.chat_history:
        print(f"Role: {msg['role']}, "
              f"Content: {msg.get('content', 'None')}")

    print("\nText Agent History:")
    for msg in new_text_agent.chat_history:
        print(f"Role: {msg['role']}, "
              f"Content: {msg.get('content', 'None')}")

    # Test 3: Continue conversation with loaded history
    print("\nTest 3: Continuing conversation with loaded history")
    
    try:
        follow_up_query = "What was the result of the previous addition?"
        print(f"Follow-up Query: {follow_up_query}")
        response = new_supervisor.chat(follow_up_query)
        print(f"Response: {response}\n")
        
        follow_up_query = "Add 17 and 90"
        print(f"Follow-up Query: {follow_up_query}")
        response = new_supervisor.chat(follow_up_query)
        print(f"Response: {response}\n")
        
    except Exception as e:
        print(f"Error in continuation: {str(e)}\n")

def main():
    try:
        test_history_management()
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()