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

# Configure to use the remote SSE MCP server 
mcp_servers = [
    {
        "type": "sse",
        "url": "https://remote.mcpservers.org/fetch",
        # "auth_token": "YOUR_TOKEN_IF_NEEDED",  # Add if the server requires auth
    }
]

agent = Agent(
    name="RemoteMCPAgent",
    llm_config=llm_config,
    mcp_servers=mcp_servers,
    system_message="You are an agent with access to remote tools via MCP.",
    use_tools=True
)

print("Available tools from remote MCP server:")
for t in agent.tools:
    print("-", t["metadata"]["function"]["name"])

print("\nType 'exit' to quit.")
while True:
    question = input("\nYou: ")
    if question.strip().lower() == "exit":
        break
    try:
        answer = agent.chat(question)
        print("Agent:", answer)
    except Exception as e:
        print("Error:", e)