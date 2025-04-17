import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from primisai.nexus.core import Agent, Supervisor

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

# MCP servers configuration for each agent
weather_mcp = {
    "type": "stdio",
    "script_path": os.path.join(os.path.dirname(__file__), "weather_server.py")
}
add_mcp = {
    "type": "sse",
    "url": "http://localhost:8000/sse",  # SSE server
}

weather_agent = Agent(
    name="WeatherAgent",
    llm_config=llm_config,
    system_message="You answer weather questions by using tools.",
    mcp_servers=[weather_mcp],
    use_tools=True,
    keep_history=True
)

add_agent = Agent(
    name="AdditionAgent",
    llm_config=llm_config,
    system_message="You answer addition and math calculation queries.",
    mcp_servers=[add_mcp],
    use_tools=True,
    keep_history=True
)

supervisor = Supervisor(
    name="MultiMCP_Supervisor",
    llm_config=llm_config,
    system_message="You delegate math and weather queries to your agents."
)

supervisor.register_agent(weather_agent)
supervisor.register_agent(add_agent)

print("\n=== Agent Hierarchy ===")
supervisor.display_agent_graph()
print("\n=== Chat with your AI Team! ===")
supervisor.start_interactive_session()