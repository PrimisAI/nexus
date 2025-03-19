import pytest
import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor

# Load environment variables
load_dotenv()

# Configuration
@pytest.fixture
def llm_config():
    return {
        'model': os.getenv('LLM_MODEL'),
        'api_key': os.getenv('LLM_API_KEY'),
        'base_url': os.getenv('LLM_BASE_URL')
    }

def test_hierarchical_structure(llm_config, capsys):
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
    assert main_supervisor.name == "MainSupervisor"
    assert sub_supervisor.name == "SubSupervisor"
    assert main_supervisor.get_registered_agents() == ["Agent1", "SubSupervisor"]
    assert sub_supervisor.get_registered_agents() == ["Agent2", "Agent3"]

    # Test chat functionality
    test_query = "Hello, can you demonstrate the hierarchical structure?"
    response = main_supervisor.chat(test_query)
    assert isinstance(response, str)
    assert len(response) > 0

    # Test display_agent_graph
    main_supervisor.display_agent_graph()
    captured = capsys.readouterr()
    assert "Supervisor: MainSupervisor" in captured.out
    assert "Assistant Supervisor: SubSupervisor" in captured.out
    assert "Agent: Agent1" in captured.out
    assert "Agent: Agent2" in captured.out
    assert "Agent: Agent3" in captured.out

def test_agent_removal(llm_config):
    supervisor = Supervisor(name="TestSupervisor", llm_config=llm_config)
    agent = Agent(name="TestAgent", llm_config=llm_config, system_message="Test agent")

    supervisor.register_agent(agent)
    assert "TestAgent" in supervisor.get_registered_agents()

    result = supervisor.remove_agent("TestAgent")
    assert result == True
    assert "TestAgent" not in supervisor.get_registered_agents()

def test_agent_retrieval(llm_config):
    supervisor = Supervisor(name="TestSupervisor", llm_config=llm_config)
    agent = Agent(name="TestAgent", llm_config=llm_config, system_message="Test agent")

    supervisor.register_agent(agent)
    retrieved_agent = supervisor.get_agent_by_name("TestAgent")
    assert retrieved_agent == agent

    non_existent_agent = supervisor.get_agent_by_name("NonExistentAgent")
    assert non_existent_agent is None