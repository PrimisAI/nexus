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

# Initialize two agents: one with history and one without
agent_1 = Agent(
    name="Agent1",
    system_message="You are a helpful assistant.",
    llm_config=llm_config,
    keep_history=True  # default behavior
)

agent_2 = Agent(
    name="Agent2",
    system_message="You are a helpful assistant.",
    llm_config=llm_config,
    keep_history=False
)

# Test queries that reference previous interactions
queries = [
    "What is the capital of France?",
    "What is the population of this city?",
    "Is this city bigger than London?"
]

if __name__ == "__main__":
    print("\nTesting Agent With History:")
    print("==========================")
    for query in queries:
        response = agent_1.chat(query)
        print(f"\nQuery: {query}")
        print(f"Response: {response}")

    print("\nTesting Agent Without History:")
    print("============================")
    for query in queries:
        response = agent_2.chat(query)
        print(f"\nQuery: {query}")
        print(f"Response: {response}")