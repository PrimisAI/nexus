# PrimisAI Nexus Framework - User Guide

## 1. Introduction
PrimisAI Nexus is a powerful Python framework for building and managing hierarchical AI agent systems. It provides a flexible architecture for creating specialized AI agents that can work together under supervisor coordination, making it ideal for complex task automation and multi-agent workflows.

### Key Features
- Hierarchical agent management
- Flexible configuration system
- Built-in conversation history tracking
- Comprehensive logging system
- Tool integration capabilities
- Support for stateful and stateless agents
- YAML-based configuration

## 2. Installation

### Via pip
```bash
pip install primisai
```

### From source
```bash
git clone git@github.com:PrimisAI/nexus.git
cd nexus
pip install -e .
```

### Environment Setup
Create a `.env` file with your LLM configuration:
```env
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key
LLM_BASE_URL=your-api-base-url
```

## 3. Core Components

### 3.1 AI Base Class
The foundation for all AI interactions in the framework.

```python
def __init__(self, llm_config: Dict[str, str]):
    """
    Initialize AI instance.
    
    Args:
        llm_config (Dict[str, str]): Configuration containing:
            - api_key: OpenAI API key
            - model: Model name
            - base_url: API base URL
    """

def generate_response(
    self,
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    use_tools: bool = False
) -> ChatCompletion:
    """
    Generate response using OpenAI's API.
    
    Args:
        messages: Conversation history
        tools: Optional tool configurations
        use_tools: Whether to use tools
        
    Returns:
        ChatCompletion: OpenAI API response
    """
```

```python
from primisai.nexus.core import AI

llm_config = {
    "api_key": "your-api-key",
    "model": "your-model",
    "base_url": "your-base-url"
}

ai = AI(llm_config=llm_config)
```

### 3.2 Agent Class
Extends AI base class with specialized capabilities.

```python
class Agent(AI):
    """Specialized AI agent with tool usage capabilities."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, str],
        workflow_id: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        system_message: Optional[str] = None,
        use_tools: bool = False,
        keep_history: bool = True,
        output_schema: Optional[Dict[str, Any]] = None,
        strict: bool = False):
    ):
        """
        Initialize Agent.
        
        Args:
            name: Agent name
            llm_config: LLM configuration
            workflow_id: Optional workflow identifier
            tools: List of available tools
            system_message: Initial system message
            use_tools: Enable tool usage
            keep_history: Maintain chat history
            output_schema (Optional[Dict[str, Any]]): Schema for agent's output format.
            strict (bool): If True, always enforce output schema.
        """
        
    def chat(self, query: str, sender_name: Optional[str] = None) -> str:
        """
        Process a chat interaction.
        
        Args:
            query: User input
            sender_name: Name of message sender
            
        Returns:
            str: Agent's response
        """
        
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get current chat history.
        
        Returns:
            List[Dict[str, str]]: Chat history
        """
```


```python
from primisai.nexus.core import Agent

agent = Agent(
    name="SpecializedAgent",
    llm_config=llm_config,
    system_message="Your specialized role description",
    tools=optional_tools,
    use_tools=True,
    keep_history=True
)
```

### 3.3 Supervisor Class
Manages and coordinates multiple agents.

```python
class Supervisor(AI):
    """Manages and coordinates multiple AI agents."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, str],
        workflow_id: Optional[str] = None,
        is_assistant: bool = False,
        system_message: Optional[str] = None
    ):
        """
        Initialize Supervisor.
        
        Args:
            name: Supervisor name
            llm_config: LLM configuration
            workflow_id: Optional workflow identifier
            is_assistant: Whether this is an assistant supervisor
            system_message: Initial system message
        """
        
    def register_agent(self, agent: Union[Agent, 'Supervisor']) -> None:
        """
        Register an agent or assistant supervisor.
        
        Args:
            agent: Agent or assistant supervisor to register
        """
        
    def chat(
        self,
        query: str,
        sender_name: Optional[str] = None,
        supervisor_chain: Optional[List[str]] = None
    ) -> str:
        """
        Process user input and coordinate responses.
        
        Args:
            query: User input
            sender_name: Name of message sender
            supervisor_chain: Chain of supervisors in delegation
            
        Returns:
            str: Final response
        """
        
    def start_interactive_session(self) -> None:
        """Start interactive chat session."""
        
    def display_agent_graph(self, indent: str = "", skip_header: bool = False) -> None:
        """
        Display hierarchical structure.
        
        Args:
            indent: Current indentation level
            skip_header: Whether to skip printing supervisor header
        """
```

```python
from primisai.nexus.core import Supervisor

supervisor = Supervisor(
    name="MainSupervisor",
    llm_config=llm_config,
    system_message="Your coordination instructions",
    workflow_id=optional_workflow_id,
    is_assistant=False
)
```

## 4. Basic Usage

### 4.1 Creating a Simple Agent System
```python
from primisai.nexus.core import Agent, Supervisor

# Create supervisor
supervisor = Supervisor(
    name="MainSupervisor",
    llm_config=llm_config,
    system_message="You are the main coordinator."
)

# Create agents
agent1 = Agent(
    name="Agent1",
    llm_config=llm_config,
    system_message="You are specialized in task A."
)

agent2 = Agent(
    name="Agent2",
    llm_config=llm_config,
    system_message="You are specialized in task B."
)

# Register agents
supervisor.register_agent(agent1)
supervisor.register_agent(agent2)

# Start interaction
response = supervisor.chat("What can you help me with?")
```

### 4.2 Interactive Sessions
```python
# Start an interactive chat session
supervisor.start_interactive_session()
```

## 5. Advanced Features

### 5.1 Hierarchical Structure
```python
# Create main supervisor
main_supervisor = Supervisor(
    name="MainSupervisor",
    llm_config=llm_config,
    system_message="Main coordination instructions"
)

# Create assistant supervisor
assistant_supervisor = Supervisor(
    name="AssistantSupervisor",
    llm_config=llm_config,
    is_assistant=True,
    system_message="Specialized domain coordination"
)

# Create specialized agents
agent1 = Agent(name="Agent1", llm_config=llm_config)
agent2 = Agent(name="Agent2", llm_config=llm_config)

# Build hierarchy
assistant_supervisor.register_agent(agent1)
assistant_supervisor.register_agent(agent2)
main_supervisor.register_agent(assistant_supervisor)

# Display hierarchy
main_supervisor.display_agent_graph()
```

### 5.2 Stateful vs Stateless Agents
```python
# Stateful agent (maintains conversation history)
stateful_agent = Agent(
    name="StatefulAgent",
    llm_config=llm_config,
    keep_history=True
)

# Stateless agent (treats each interaction independently)
stateless_agent = Agent(
    name="StatelessAgent",
    llm_config=llm_config,
    keep_history=False
)
```

## 6. Configuration Management

### 6.1 YAML Configuration
```yaml
# config.yaml
supervisor:
  name: MainSupervisor
  type: supervisor
  llm_config:
    model: ${LLM_MODEL}
    api_key: ${LLM_API_KEY}
    base_url: ${LLM_BASE_URL}
  system_message: "Main supervisor instructions"
  children:
    - name: Agent1
      type: agent
      llm_config:
        model: ${LLM_MODEL}
        api_key: ${LLM_API_KEY}
        base_url: ${LLM_BASE_URL}
      system_message: "Agent1 instructions"
      tools:
        - name: tool_name
          type: function
          python_path: path.to.function
          description: "Tool description"
```

### 6.2 Loading Configuration
```python
from primisai.nexus.config import load_yaml_config, AgentFactory

config = load_yaml_config('path/to/config.yaml')
factory = AgentFactory()
supervisor = factory.create_from_config(config)
```

## 7. Tools Integration

### 7.1 Creating Tools
```python
# Define tool function
def calculator(num1: int, num2: int, operation: str) -> float:
    if operation == "add": return num1 + num2
    elif operation == "multiply": return num1 * num2
    raise ValueError("Unsupported operation")

# Define tool metadata
calculator_metadata = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "num1": {"type": "integer"},
                "num2": {"type": "integer"},
                "operation": {
                    "type": "string",
                    "enum": ["add", "multiply"]
                }
            },
            "required": ["num1", "num2", "operation"]
        }
    }
}

# Create tool-enabled agent
calculator_agent = Agent(
    name="CalculatorAgent",
    llm_config=llm_config,
    tools=[{"tool": calculator, "metadata": calculator_metadata}],
    use_tools=True
)
```

## 8. Real-World Examples

### 8.1 Multiple Tool Integration
This example demonstrates how to create an agent with multiple tools and a supervisor to manage complex tasks.

```python
from primisai.nexus.core import Agent, Supervisor

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

# Create and set up supervisor
supervisor = Supervisor(
    name="Multi_Tool_Supervisor",
    llm_config=llm_config,
    system_message="You are a helpful supervisor who can assign tasks to agents."
)

supervisor.register_agent(calculator_agent)
supervisor.register_agent(text_agent)

# Example usage
query = """I need three things done:
1. Add 15 and 27
2. Convert 'Hello World' to uppercase
3. Multiply 8 by 6"""

response = supervisor.chat(query)
print(f"Response: {response}")
```

### 8.2 Context-Aware Task Management
This example shows how to implement a task management system with context awareness using YAML configuration.

```yaml
# config.yaml
supervisor:
  name: ContextTaskManager
  type: supervisor
  llm_config:
    model: ${LLM_MODEL}
    api_key: ${LLM_API_KEY}
    base_url: ${LLM_BASE_URL}
  system_message: "You are the context-aware task management supervisor."
  children:
    - name: StatefulTaskManager
      type: agent
      llm_config:
        model: ${LLM_MODEL}
        api_key: ${LLM_API_KEY}
        base_url: ${LLM_BASE_URL}
      system_message: "You are a stateful task manager that remembers context."
      keep_history: true
      tools:
        - name: add_task_with_context
          type: function
          python_path: task_tools.add_task_with_context
          description: "Add a task with context information"
          parameters:
            task:
              type: string
              description: "The task to be added"
            context:
              type: string
              description: "The context/category for the task"
```

```python
# task_tools.py
context_tasks = {}

def add_task_with_context(task: str, context: str) -> str:
    if context not in context_tasks:
        context_tasks[context] = []
    context_tasks[context].append(task)
    return f"Task added to {context}: {task}"

def list_context_tasks(context: str) -> str:
    if context not in context_tasks:
        return f"No tasks found in context: {context}"
    tasks = context_tasks[context]
    return "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))

def get_contexts() -> str:
    if not context_tasks:
        return "No contexts available"
    return "\n".join(f"- {context} ({len(tasks)} tasks)" 
                    for context, tasks in context_tasks.items())

# main.py
from primisai.nexus.config import load_yaml_config, AgentFactory

config = load_yaml_config('config.yaml')
factory = AgentFactory()
context_manager = factory.create_from_config(config)

# Example usage
context_manager.chat("Add a task 'Update documentation' to the 'Development' context")
context_manager.chat("What tasks are in the Development context?")
```

### 8.3 Hierarchical Agent Structure with History Tracking
This example demonstrates how to create a complex hierarchical structure with history tracking.

```python
from primisai.nexus.core import Agent, Supervisor

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

# Create assistant supervisor
domain_supervisor = Supervisor(
    name="DomainSupervisor",
    llm_config=llm_config,
    is_assistant=True,
    system_message="You manage specialized domain tasks."
)

# Create main supervisor
main_supervisor = Supervisor(
    name="MainSupervisor",
    llm_config=llm_config,
    system_message="You coordinate all operations."
)

# Build hierarchy
domain_supervisor.register_agent(math_agent)
domain_supervisor.register_agent(writing_agent)
main_supervisor.register_agent(domain_supervisor)

# Display hierarchy
main_supervisor.display_agent_graph()

# Example complex interaction
query = """I need two things:
1. Calculate 25 * 4
2. Write a haiku about mathematics"""

response = main_supervisor.chat(query)

# View conversation history
print("\nMain Supervisor History:")
for msg in main_supervisor.get_chat_history():
    print(f"Role: {msg['role']}")
    print(f"Content: {msg['content']}\n")

print("\nMath Agent History:")
for msg in math_agent.get_chat_history():
    print(f"Role: {msg['role']}")
    print(f"Content: {msg['content']}\n")
```

### 8.4 Terminal Command Execution Agent
This example shows how to create an agent that can execute terminal commands with proper error handling.

```python
import subprocess
from primisai.nexus.core import Agent

# Tool definition
def execute_command(argument: str):
    try:
        result = subprocess.run(
            argument,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return {"status": "success", "output": output.strip()}
        else:
            return {"status": "error", "output": output.strip()}
    except Exception as e:
        return {"status": "error", "output": str(e)}

command_tool_metadata = {
    "type": "function",
    "function": {
        "name": "execute_command",
        "description": "Execute a command on the terminal",
        "parameters": {
            "type": "object",
            "properties": {
                "argument": {
                    "type": "string",
                    "description": "Command to execute"
                }
            },
            "required": ["argument"]
        }
    }
}

# Create command execution agent
terminal_agent = Agent(
    name="TerminalAgent",
    llm_config=llm_config,
    system_message="You can execute terminal commands safely.",
    tools=[{"tool": execute_command, "metadata": command_tool_metadata}],
    use_tools=True
)

# Example usage
response = terminal_agent.chat("List files in the current directory")
print(response)
```

### 8.5 Stateful vs Stateless Agents Comparison
This example demonstrates the difference between agents that maintain conversation history and those that don't.

```python
from primisai.nexus.core import Agent

# Initialize two agents with different history settings
stateful_agent = Agent(
    name="StatefulAgent",
    llm_config=llm_config,
    system_message="You are a helpful assistant.",
    keep_history=True  # default behavior
)

stateless_agent = Agent(
    name="StatelessAgent",
    llm_config=llm_config,
    system_message="You are a helpful assistant.",
    keep_history=False
)

# Test queries that reference previous interactions
queries = [
    "What is the capital of France?",
    "What is the population of this city?",
    "Is this city bigger than London?"
]

print("\nTesting Stateful Agent (remembers context):")
print("=======================================")
for query in queries:
    response = stateful_agent.chat(query)
    print(f"\nQuery: {query}")
    print(f"Response: {response}")

print("\nTesting Stateless Agent (no context memory):")
print("=========================================")
for query in queries:
    response = stateless_agent.chat(query)
    print(f"\nQuery: {query}")
    print(f"Response: {response}")
```

### 8.6 Multi-Argument Function Calling
This example shows how to create and use tools with multiple arguments.

```python
from primisai.nexus.core import Agent

# Define a complex tool with multiple arguments
complex_calculator_metadata = {
    "type": "function",
    "function": {
        "name": "complex_calculate",
        "description": "Perform mathematical operations with multiple numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "num1": {
                    "type": "integer",
                    "description": "First number"
                },
                "num2": {
                    "type": "integer",
                    "description": "Second number"
                },
                "num3": {
                    "type": "integer",
                    "description": "Third number"
                },
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["sum", "product", "average"]
                }
            },
            "required": ["num1", "num2", "num3", "operation"]
        }
    }
}

def complex_calculate(num1: int, num2: int, num3: int, operation: str) -> float:
    if operation == "sum":
        return num1 + num2 + num3
    elif operation == "product":
        return num1 * num2 * num3
    elif operation == "average":
        return (num1 + num2 + num3) / 3
    raise ValueError(f"Unsupported operation: {operation}")

# Create agent with the complex calculator tool
math_agent = Agent(
    name="ComplexMathAgent",
    llm_config=llm_config,
    system_message="You are a mathematical agent capable of complex calculations.",
    tools=[{"tool": complex_calculate, "metadata": complex_calculator_metadata}],
    use_tools=True
)

# Example usage
query = "Calculate the average of numbers 10, 15, and 20"
response = math_agent.chat(query)
print(f"Query: {query}")
print(f"Response: {response}")
```

### 8.7 Multi-Tool Agent
This example demonstrates how to create a single agent with multiple diverse tools.

```python
from primisai.nexus.core import Agent

# Tool 1: Text Analysis
text_analysis_metadata = {
    "type": "function",
    "function": {
        "name": "analyze_text",
        "description": "Analyze text properties",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["word_count", "char_count", "sentence_count"]
                }
            },
            "required": ["text", "analysis_type"]
        }
    }
}

def analyze_text(text: str, analysis_type: str) -> int:
    if analysis_type == "word_count":
        return len(text.split())
    elif analysis_type == "char_count":
        return len(text)
    elif analysis_type == "sentence_count":
        return len([s for s in text.split('.') if s.strip()])
    raise ValueError("Invalid analysis type")

# Tool 2: Data Conversion
data_conversion_metadata = {
    "type": "function",
    "function": {
        "name": "convert_units",
        "description": "Convert between different units",
        "parameters": {
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "Value to convert"},
                "from_unit": {
                    "type": "string",
                    "enum": ["km", "miles", "kg", "lbs"]
                },
                "to_unit": {
                    "type": "string",
                    "enum": ["km", "miles", "kg", "lbs"]
                }
            },
            "required": ["value", "from_unit", "to_unit"]
        }
    }
}

def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x * 0.453592
    }
    
    if (from_unit, to_unit) in conversions:
        return conversions[(from_unit, to_unit)](value)
    raise ValueError("Unsupported conversion")

# Tool 3: Date Operations
date_operations_metadata = {
    "type": "function",
    "function": {
        "name": "date_operation",
        "description": "Perform date calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "operation": {
                    "type": "string",
                    "enum": ["add_days", "subtract_days"]
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days"
                }
            },
            "required": ["date", "operation", "days"]
        }
    }
}

from datetime import datetime, timedelta

def date_operation(date: str, operation: str, days: int) -> str:
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    if operation == "add_days":
        result = date_obj + timedelta(days=days)
    elif operation == "subtract_days":
        result = date_obj - timedelta(days=days)
    else:
        raise ValueError("Invalid operation")
    return result.strftime("%Y-%m-%d")

# Create multi-tool agent
multi_tool_agent = Agent(
    name="MultiToolAgent",
    llm_config=llm_config,
    system_message="""You are a versatile agent capable of:
    1. Text analysis
    2. Unit conversions
    3. Date calculations
    Use the appropriate tool based on the user's request.""",
    tools=[
        {"tool": analyze_text, "metadata": text_analysis_metadata},
        {"tool": convert_units, "metadata": data_conversion_metadata},
        {"tool": date_operation, "metadata": date_operations_metadata}
    ],
    use_tools=True
)

# Example usage
queries = [
    "How many words are in the text 'The quick brown fox jumps over the lazy dog'?",
    "Convert 100 kilometers to miles",
    "What date is 30 days from 2024-03-15?"
]

for query in queries:
    print(f"\nQuery: {query}")
    response = multi_tool_agent.chat(query)
    print(f"Response: {response}")
```

### 8.8 Complex Tool Implementation with Error Handling and Validation
This example shows a more sophisticated tool implementation with proper error handling and input validation.

```python
from typing import Dict, Any, Optional, Union
import json
from datetime import datetime
import re

# Complex tool for data processing
data_processor_metadata = {
    "type": "function",
    "function": {
        "name": "process_data",
        "description": "Process and validate various types of data",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Data to process (JSON string)"
                },
                "data_type": {
                    "type": "string",
                    "enum": ["email", "phone", "date", "address"],
                    "description": "Type of data to validate"
                },
                "format_output": {
                    "type": "boolean",
                    "description": "Whether to format the output"
                }
            },
            "required": ["data", "data_type"]
        }
    }
}

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

def validate_email(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_address(address: Dict[str, str]) -> str:
    return f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"

def process_data(data: str, data_type: str, format_output: Optional[bool] = False) -> Dict[str, Any]:
    try:
        # Parse input data
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            parsed_data = data

        result = {
            "valid": False,
            "formatted_data": None,
            "error": None
        }

        # Process based on data type
        if data_type == "email":
            result["valid"] = validate_email(parsed_data)
            if result["valid"] and format_output:
                result["formatted_data"] = parsed_data.lower()

        elif data_type == "phone":
            result["valid"] = validate_phone(parsed_data)
            if result["valid"] and format_output:
                # Format phone number: +1-XXX-XXX-XXXX
                digits = re.sub(r'\D', '', parsed_data)
                if len(digits) == 10:
                    result["formatted_data"] = f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                else:
                    result["formatted_data"] = parsed_data

        elif data_type == "date":
            result["valid"] = validate_date(parsed_data)
            if result["valid"] and format_output:
                date_obj = datetime.strptime(parsed_data, "%Y-%m-%d")
                result["formatted_data"] = date_obj.strftime("%B %d, %Y")

        elif data_type == "address":
            if isinstance(parsed_data, dict) and all(k in parsed_data for k in ["street", "city", "state", "zip"]):
                result["valid"] = True
                if format_output:
                    result["formatted_data"] = format_address(parsed_data)
            else:
                raise DataValidationError("Invalid address format")

        return result

    except DataValidationError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"Processing error: {str(e)}"}

# Create agent with complex data processing tool
data_processing_agent = Agent(
    name="DataProcessor",
    llm_config=llm_config,
    system_message="You are a data processing specialist with advanced validation capabilities.",
    tools=[{"tool": process_data, "metadata": data_processor_metadata}],
    use_tools=True
)

# Example usage
test_queries = [
    'Validate and format the email "user@example.com"',
    'Validate and format the phone number "1234567890"',
    'Validate and format the date "2024-03-15"',
    '''Validate and format the address {
        "street": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701"
    }'''
]

for query in test_queries:
    print(f"\nQuery: {query}")
    response = data_processing_agent.chat(query)
    print(f"Response: {response}")
```

### 8.9 Schema-Aware Agents
This example demonstrates how to create agents with structured outputs using output schemas and validation.

```python
from primisai.nexus.core import Agent, Supervisor

# Example 1: Code Generation Agent with Schema
code_agent = Agent(
    name="CodeWriter",
    llm_config=llm_config,
    system_message="You are a skilled programmer who writes clean, documented code.",
    output_schema='''{
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Explanation of the code's purpose"
            },
            "code": {
                "type": "string",
                "description": "The actual code implementation"
            },
            "language": {
                "type": "string",
                "description": "Programming language used"
            }
        },
        "required": ["description", "code"]
    }''',
    strict=True  # Always enforce schema
)

# Example 2: Analysis Agent with Non-Strict Schema
analysis_agent = Agent(
    name="DataAnalyst",
    llm_config=llm_config,
    system_message="You analyze data and provide structured insights.",
    output_schema='''{
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief analysis summary"
            },
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key findings"
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggested actions"
            }
        },
        "required": ["summary", "key_points"]
    }''',
    strict=False  # Allow fallback to unstructured responses
)

# Example 3: Content Creation Agent with Metadata Schema
content_agent = Agent(
    name="ContentCreator",
    llm_config=llm_config,
    system_message="You create structured content with metadata.",
    output_schema='''{
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Content title"
            },
            "content": {
                "type": "string",
                "description": "Main content body"
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "readingTime": {"type": "string"}
                }
            }
        },
        "required": ["title", "content"]
    }''',
    strict=True
)

# Create a supervisor to manage schema-aware agents
supervisor = Supervisor(
    name="ContentSupervisor",
    llm_config=llm_config,
    system_message="You coordinate between different content creation and analysis tasks."
)

supervisor.register_agent(code_agent)
supervisor.register_agent(analysis_agent)
supervisor.register_agent(content_agent)
```

### 8.10 Task Management System with Structured Outputs
This example shows how to build a task management system where each agent produces structured outputs for reliable downstream processing.

```python
from primisai.nexus.core import Agent, Supervisor

# Task Creation Agent with Schema
task_creator = Agent(
    name="TaskCreator",
    llm_config=llm_config,
    system_message="You create well-structured task definitions.",
    output_schema='''{
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Unique identifier for the task"
            },
            "title": {
                "type": "string",
                "description": "Task title"
            },
            "description": {
                "type": "string",
                "description": "Detailed task description"
            },
            "requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of requirements"
            },
            "estimated_hours": {
                "type": "number",
                "description": "Estimated hours to complete"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"]
            }
        },
        "required": ["task_id", "title", "description", "priority"]
    }''',
    strict=True
)

# Task Analyzer with Complex Schema
task_analyzer = Agent(
    name="TaskAnalyzer",
    llm_config=llm_config,
    system_message="You analyze tasks and provide structured assessments.",
    output_schema='''{
        "type": "object",
        "properties": {
            "analysis": {
                "type": "object",
                "properties": {
                    "complexity_score": {
                        "type": "integer",
                        "description": "Task complexity (1-10)"
                    },
                    "risk_factors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "factor": {"type": "string"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "mitigation": {"type": "string"}
                            }
                        }
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "recommendations": {
                "type": "object",
                "properties": {
                    "team_size": {"type": "integer"},
                    "skill_requirements": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "suggested_timeline": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "milestones": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "date": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "required": ["analysis", "recommendations"]
    }''',
    strict=True
)

# Progress Reporter with Metrics Schema
progress_reporter = Agent(
    name="ProgressReporter",
    llm_config=llm_config,
    system_message="You generate structured progress reports with metrics.",
    output_schema='''{
        "type": "object",
        "properties": {
            "project_metrics": {
                "type": "object",
                "properties": {
                    "completion_percentage": {"type": "number"},
                    "hours_logged": {"type": "number"},
                    "tasks_completed": {"type": "integer"},
                    "tasks_remaining": {"type": "integer"}
                }
            },
            "milestone_status": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "milestone": {"type": "string"},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "delayed"]},
                        "actual_vs_planned": {"type": "string"}
                    }
                }
            },
            "key_achievements": {
                "type": "array",
                "items": {"type": "string"}
            },
            "blockers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "impact": {"type": "string"},
                        "resolution_plan": {"type": "string"}
                    }
                }
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["project_metrics", "milestone_status", "next_steps"]
    }''',
    strict=True
)

# Create Project Manager Supervisor
project_manager = Supervisor(
    name="ProjectManager",
    llm_config=llm_config,
    system_message="""You are a project manager coordinating task creation, analysis, and reporting.
    Ensure all outputs maintain their structured format for reliable project tracking."""
)

# Register agents
project_manager.register_agent(task_creator)
project_manager.register_agent(task_analyzer)
project_manager.register_agent(progress_reporter)

```