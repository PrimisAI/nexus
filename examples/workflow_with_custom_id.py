"""
Simple workflow example demonstrating custom workflow_id with one supervisor and one agent.

This example shows:
1. How to create a workflow with a custom workflow_id
2. Basic interaction between supervisor and agent
3. Persistent storage across sessions
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

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

def create_simple_workflow(workflow_id: str):
    """
    Create a simple workflow with custom workflow_id.
    
    Args:
        workflow_id (str): Custom workflow identifier
    
    Returns:
        Supervisor: The supervisor managing the workflow
    """
    print(f"Creating workflow: {workflow_id}")
    
    # Create supervisor with custom workflow_id
    supervisor = Supervisor(
        name="TaskSupervisor",
        llm_config=llm_config,
        workflow_id=workflow_id,
        system_message="You are a helpful supervisor managing a writing assistant."
    )
    
    # Create a single agent
    writer_agent = Agent(
        name="WriterAgent",
        llm_config=llm_config,
        system_message="You are a creative writing assistant who helps with various writing tasks."
    )
    
    # Register the agent
    supervisor.register_agent(writer_agent)
    
    print(f"✓ Workflow '{workflow_id}' created successfully!")
    return supervisor

def main():
    """Main function to run the simple workflow example."""
    
    # Get workflow_id from user or use default
    if len(sys.argv) > 1:
        workflow_id = sys.argv[1]
    else:
        workflow_id = input("Enter workflow ID (or press Enter for 'simple_writing_workflow'): ").strip()
        if not workflow_id:
            workflow_id = "simple_writing_workflow"
    
    # Create the workflow
    supervisor = create_simple_workflow(workflow_id)
    
    # Show workflow structure
    print(f"\nWorkflow Structure:")
    supervisor.display_agent_graph()
    
    # Show workflow information
    print(f"\nWorkflow Information:")
    print(f"├── Workflow ID: {workflow_id}")
    print(f"├── Supervisor: TaskSupervisor")
    print(f"├── Agent: WriterAgent")
    print(f"└── Storage: nexus_workflows/{workflow_id}/")
    
    # Start interactive session
    print(f"\nStarting interactive session with workflow '{workflow_id}'")
    print("Type 'exit' to quit, 'info' to see workflow details")
    print("-" * 50)
    
    while True:
        user_input = input(f"\n[{workflow_id}] You: ").strip()
        
        if user_input.lower() == 'exit':
            print(f"Session ended. Workflow '{workflow_id}' has been saved.")
            break
        elif user_input.lower() == 'info':
            print(f"\nWorkflow: {workflow_id}")
            print(f"Messages in history: {len(supervisor.chat_history)}")
            supervisor.display_agent_graph()
        elif user_input:
            try:
                response = supervisor.chat(user_input)
                print(f"TaskSupervisor: {response}")
            except Exception as e:
                print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()