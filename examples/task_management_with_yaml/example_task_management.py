import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from primisai.nexus.config import load_yaml_config, AgentFactory

# Load environment variables
load_dotenv()

# Load and process the YAML configuration
config = load_yaml_config('examples/task_management_with_yaml/config.yaml')

# Create the agent structure from YAML
factory = AgentFactory()
task_manager = factory.create_from_config(config)

# Function to handle user input and agent responses
def chat_with_agents(query: str):
    response = task_manager.chat(query)
    print(f"Task Manager: {response}")

# Main interaction loop
if __name__ == "__main__":
    print("Welcome to the Task Management System!")
    print("You can interact with the following agents:")
    task_manager.display_agent_graph()
    print("Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        chat_with_agents(user_input)