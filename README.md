# Nexus

Nexus is a powerful and flexible Python package for managing AI agents and coordinating complex tasks using LLMs. It provides a robust framework for creating, managing, and interacting with multiple specialized AI agents under the supervision of a central coordinator.

## Features

- **AI Base Class**: A foundational class for AI interactions.
- **Agent Class**: Extends the AI base class with additional features for specialized tasks.
- **Supervisor Class**: Manages multiple agents, coordinates tasks, and handles user interactions.
- **Debugger Utility**: Integrated debugging capabilities for logging and troubleshooting.
- **Flexible Configuration**: Easy-to-use configuration options for language models and agents.
- **Interactive Sessions**: Built-in support for interactive chat sessions with the AI system.

## Installation

You can install Nexus using pip:

```bash
pip install -e .
```

## Quick Start

Here's a simple example to get you started with Nexus:

```python
from nexus.core import AI, Agent, Supervisor
from nexus.utils import Debugger

# Configure your OpenAI API key
llm_config = {
    "api_key": "your-api-key-here",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",
}

# Create a supervisor
supervisor = Supervisor("MainSupervisor", llm_config)

# Create and register agents
agent1 = Agent("Agent1", llm_config, system_message="You are a helpful assistant.")
agent2 = Agent("Agent2", llm_config, system_message="You are a creative writer.")

supervisor.register_agent(agent1)
supervisor.register_agent(agent2)

# Start an interactive session
supervisor.start_interactive_session()
```

## Documentation

For detailed documentation on each module and class, please refer to the inline docstrings in the source code.


## Advanced Usage

Nexus allows for complex interactions between multiple agents. You can create specialized agents for different tasks, register them with a supervisor, and let the supervisor manage the flow of information and task delegation.

```python
# Example of creating a specialized agent with tools
tools = [
    {
        "metadata": {
            "name": "search_tool",
            "description": "Searches the internet for information"
        },
        "tool": some_search_function
    }
]

research_agent = Agent("Researcher", llm_config, tools=tools, system_message="You are a research assistant.", use_tools=True)
supervisor.register_agent(research_agent)
```

## License

This project is licensed under the MIT License.