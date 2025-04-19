import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

# Setup MCP server config (local, no auth)
mcp_servers = [
    {"type": "sse", "url": "http://localhost:8000/sse", "auth_token": None}
]

agent = Agent(
    name="MCPAgent",
    llm_config=llm_config,
    system_message="You are an agent using MCP tools.",
    mcp_servers=mcp_servers
)

print("=== Tools discovered from MCP server ===")
for t in agent.tools:
    meta = t["metadata"]["function"]
    print(f"- {meta['name']}: {meta.get('description')}")
print("")

# Find the "add" tool from MCP
add_tool = next((t for t in agent.tools if t["metadata"]["function"]["name"] == "add"), None)
if not add_tool:
    print("No 'add' tool found!")
    exit(1)

print("Calling 'add' tool from agent (add(2, 3)):")
result = add_tool["tool"](a=2, b=3)
print("Result:", result)

# Now test MCP tool update (simulate adding new tool in MCP server before calling)
input("\nAdd another tool in your running MCP server and press enter to update MCP tools...")

agent.update_mcp_tools()
print("\n=== Tools after update ===")
for t in agent.tools:
    meta = t["metadata"]["function"]
    print(f"- {meta['name']}: {meta.get('description')}")