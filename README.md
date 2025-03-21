# PrimisAI Nexus
[![arXiv](https://img.shields.io/badge/arXiv-2502.19091-b31b1b.svg)](https://arxiv.org/abs/2502.19091) [![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/nexus-a-lightweight-and-scalable-multi-agent/code-generation-on-verilogeval)](https://paperswithcode.com/sota/code-generation-on-verilogeval?p=nexus-a-lightweight-and-scalable-multi-agent) [![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/nexus-a-lightweight-and-scalable-multi-agent/code-generation-on-humaneval)](https://paperswithcode.com/sota/code-generation-on-humaneval?p=nexus-a-lightweight-and-scalable-multi-agent)

![Tests](https://github.com/PrimisAI/nexus/actions/workflows/tests.yaml/badge.svg) ![Continuous Delivery](https://github.com/PrimisAI/nexus/actions/workflows/cd.yaml/badge.svg) ![PyPI - Version](https://img.shields.io/pypi/v/primisai) ![PyPI - Downloads](https://img.shields.io/pypi/dm/primisai) ![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FPrimisAI%2Fnexus%2Fmain%2Fpyproject.toml) ![GitHub License](https://img.shields.io/github/license/PrimisAI/nexus)


PrimisAI Nexus is a powerful and flexible Python package for managing AI agents and coordinating complex tasks using LLMs. It provides a robust framework for creating, managing, and interacting with multiple specialized AI agents under the supervision of a central coordinator.

<div align="center">
<img src="./examples/images/performance-coding.png" width="275"> <img src="./examples/images/performance-timing-closure.png" width="461">
</div>

## Features

- **AI Base Class**: A foundational class for AI interactions.
- **Agent Class**: Extends the AI base class with additional features for specialized tasks.
- **Supervisor Class**: Manages multiple agents, coordinates tasks, and handles user interactions.
- **Hierarchical Supervision**: Support for main and assistant supervisors enabling complex task hierarchies.
- **Persistent History**: Built-in conversation history management with JSONL storage.
- **Integrated Logging**: Organized logging system within workflow structure.
- **Debugger Utility**: Integrated debugging capabilities for logging and troubleshooting.
- **Flexible Configuration**: Easy-to-use configuration options for language models and agents.
- **Flexible LLM Parameters**: Direct control over all language model parameters through configuration.
- **Interactive Sessions**: Built-in support for interactive chat sessions with the AI system.
- **YAML Configuration**: Define complex agent hierarchies using YAML files for easy setup and modification.

## Installation

You can install PrimisAI Nexus directly from PyPI using pip:

```bash
pip install primisai
```

### Building from Source

If you prefer to build the package from source, clone the repository and install it with pip:

```bash
git clone git@github.com:PrimisAI/nexus.git
cd nexus
pip install -e .
```

## Quick Start

Here's a simple example to get you started with Nexus:

```python
from primisai.nexus.core import AI, Agent, Supervisor
from primisai.nexus.utils.debugger import Debugger

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
supervisor.display_agent_graph()
supervisor.start_interactive_session()
```

## YAML Configuration

PrimisAI Nexus supports defining complex agent hierarchies using YAML configuration files. This feature allows for easy setup and modification of agent structures without changing the Python code.

### Example YAML Configuration

Here's a simple example of a YAML configuration file:

```yaml
supervisor:
  name: TaskManager
  type: supervisor
  llm_config:
    model: ${LLM_MODEL}
    api_key: ${LLM_API_KEY}
    base_url: ${LLM_BASE_URL}
  system_message: "You are the task management supervisor."
  children:
    - name: TaskCreator
      type: agent
      llm_config:
        model: ${LLM_MODEL}
        api_key: ${LLM_API_KEY}
        base_url: ${LLM_BASE_URL}
      system_message: "You are responsible for creating new tasks."
      keep_history: true
      tools:
        - name: add_task
          type: function
          python_path: examples.task_management_with_yaml.task_tools.add_task
```

The `keep_history` parameter allows you to control whether an agent maintains conversation history between interactions. When set to `False`, the agent treats each query independently, useful for stateless operations. When `True` (default), the agent maintains context from previous interactions.

To use this YAML configuration:

```python
from primisai.nexus.config import load_yaml_config, AgentFactory

# Load the YAML configuration
config = load_yaml_config('path/to/your/config.yaml')

# Create the agent structure
factory = AgentFactory()
task_manager = factory.create_from_config(config)

# Start an interactive session
task_manager.start_interactive_session()
```

For a more detailed example of YAML configuration, check out the [task management example](examples/task_management_with_yaml).

### Benefits of YAML Configuration

- **Flexibility**: Easily modify agent structures without changing Python code.
- **Readability**: YAML configurations are human-readable and easy to understand.
- **Scalability**: Define complex hierarchies of supervisors and agents in a clear, structured manner.
- **Separation of Concerns**: Keep agent definitions separate from application logic.

## Documentation

For detailed documentation on each module and class, please refer to the inline docstrings in the source code.

## History and Logging
PrimisAI Nexus provides comprehensive history management and logging capabilities organized within workflow directories:

```bash
nexus_workflows/
├── workflow_123/              # Workflow specific directory
│   ├── history.jsonl         # Conversation history
│   └── logs/                 # Workflow logs
│       ├── MainSupervisor.log
│       ├── AssistantSupervisor.log
│       └── Agent1.log
└── standalone_logs/          # Logs for agents not in workflows
    └── StandaloneAgent.log
```

## Advanced Usage

PrimisAI Nexus allows for complex interactions between multiple agents. You can create specialized agents for different tasks, register them with a supervisor, and let the supervisor manage the flow of information and task delegation.

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

### Hierarchical Supervisor Structure

PrimisAI Nexus supports a hierarchical supervisor structure with two types of supervisors:

1. Main Supervisor: The root supervisor that manages the overall workflow

2. Assistant Supervisor: Specialized supervisors that handle specific task domains

Here's how to create and use different types of supervisors:

```python
# Create a main supervisor with a specific workflow ID
main_supervisor = Supervisor(
    name="MainSupervisor",
    llm_config=llm_config,
    workflow_id="custom_workflow_123"
)

# Create an assistant supervisor
assistant_supervisor = Supervisor(
    name="AnalysisManager",
    llm_config=llm_config,
    is_assistant=True,
    system_message="You manage data analysis tasks."
)

# Create agents
data_agent = Agent("DataAnalyst", llm_config, system_message="You analyze data.")
viz_agent = Agent("Visualizer", llm_config, system_message="You create visualizations.")

# Register assistant supervisor with main supervisor
main_supervisor.register_agent(assistant_supervisor)

# Register agents with assistant supervisor
assistant_supervisor.register_agent(data_agent)
assistant_supervisor.register_agent(viz_agent)

# Display the complete hierarchy
main_supervisor.display_agent_graph()
```

The above code creates a hierarchical structure where:
- Main Supervisor manages the overall workflow
- Assistant Supervisor handles specialized tasks
- Agents perform specific operations

The `display_agent_graph()` output will show:

```
Main Supervisor: MainSupervisor
│
└── Assistant Supervisor: AnalysisManager
    │
    ├── Agent: DataAnalyst
    │   └── No tools available
    │
    └── Agent: Visualizer
        └── No tools available
```

Each workflow is automatically assigned a unique ID and maintains its conversation history in a dedicated directory structure:

```
custom_workflow_123/
├── history.jsonl
└── logs
    ├── AnalysisManager.log
    ├── DataAnalyst.log
    ├── MainSupervisor.log
    └── Visualizer.log
```

All interactions, delegations, and tool usage are automatically logged and stored in the workflow directory, providing complete visibility into the decision-making process and execution flow.

## Citation
If you find Nexus useful, please consider citing our preprint.
```bibtex
@article{sami2025nexus,
  title={Nexus: A Lightweight and Scalable Multi-Agent Framework for Complex Tasks Automation},
  author={Sami, Humza and ul Islam, Mubashir and Charas, Samy and Gandhi, Asav and Gaillardon, Pierre-Emmanuel and Tenace, Valerio},
  journal={arXiv preprint arXiv:2502.19091},
  year={2025}
}
```
## License

This project is licensed under the MIT License.
