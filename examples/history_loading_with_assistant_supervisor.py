import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor
from primisai.nexus.history import HistoryManager

# Load environment variables
load_dotenv()

# Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

def test_hierarchical_structure():
    # Create agents
    agent1 = Agent(name="Agent1", llm_config=llm_config, system_message="You are Agent1.")
    agent2 = Agent(name="Agent2", llm_config=llm_config, system_message="You are Agent2.")
    agent3 = Agent(name="Agent3", llm_config=llm_config, system_message="You are Agent3.")

    # Create sub-supervisor
    sub_supervisor = Supervisor(
        name="SubSupervisor", 
        system_message="You are a sub-supervisor managing Agent2 and Agent3.",
        llm_config=llm_config,
        is_assistant=True)
    sub_supervisor.register_agent(agent2)
    sub_supervisor.register_agent(agent3)

    # Create main supervisor
    main_supervisor = Supervisor(
        name="MainSupervisor", 
        system_message="You are the main supervisor managing Agent1 and SubSupervisor.",
        llm_config=llm_config)
    main_supervisor.register_agent(agent1)
    main_supervisor.register_agent(sub_supervisor)

    # Test the structure
    print("Testing hierarchical structure:")
    print(f"Main Supervisor: {main_supervisor.name}")
    print(f"Registered agents with Main Supervisor: {main_supervisor.get_registered_agents()}")
    print(f"Sub-Supervisor: {sub_supervisor.name}")
    print(f"Registered agents with Sub-Supervisor: {sub_supervisor.get_registered_agents()}")

    # Test chat functionality
    test_query = "Hello, can you demonstrate the hierarchical structure by asking all the agents?"
    print(f"\nTesting chat with query: '{test_query}'")
    response = main_supervisor.chat(test_query)
    print(f"Response: {response}")

    # Display the agent graph
    print("\nAgent Graph:")
    main_supervisor.display_agent_graph()
    
    workflow_id = main_supervisor.workflow_id
    history_manager = HistoryManager(workflow_id)
    
    print("MainSupervisor: \n", history_manager.load_chat_history("MainSupervisor"))
    print("\nSubSupervisor: \n", history_manager.load_chat_history("SubSupervisor"))
    print("\nAgent1: \n", history_manager.load_chat_history("Agent1"))
    print("\nAgent2: \n", history_manager.load_chat_history("Agent2"))
    print("\nAgent3: \n", history_manager.load_chat_history("Agent3"))

if __name__ == "__main__":
    test_hierarchical_structure()