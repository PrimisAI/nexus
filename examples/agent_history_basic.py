"""
Example: Standalone Agent with working persistent history.jsonl
"""

import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent
from primisai.nexus.history import HistoryManager, EntityType

load_dotenv()

llm_config = {
    "model": os.getenv('LLM_MODEL'),
    "api_key": os.getenv('LLM_API_KEY'),
    "base_url": os.getenv('LLM_BASE_URL')
}

WORKFLOW_ID = "agent_history_demo"
system_message = "You are a friendly assistant who remembers our conversation history."

def create_workflow_dir():
    wf_dir = os.path.join("nexus_workflows", WORKFLOW_ID)
    os.makedirs(wf_dir, exist_ok=True)
    history_file = os.path.join(wf_dir, "history.jsonl")
    if not os.path.exists(history_file):
        open(history_file, "w").close()

def main():
    print(f"\n--- Standalone Agent with Persistent History ---")
    print(f"Workflow ID: {WORKFLOW_ID}\n")

    create_workflow_dir()

    # Instantiate agent (standalone)
    agent = Agent(
        name="SoloAgent",
        llm_config=llm_config,
        workflow_id=WORKFLOW_ID,
        system_message=system_message,
        keep_history=True
    )

    # ---- CRUCIAL: Manually attach a working history_manager ----
    agent.history_manager = HistoryManager(WORKFLOW_ID)
    # Save system message to history.jsonl if it's not already present
    if agent.system_message and not agent.history_manager.has_system_message(agent.name):
        agent.history_manager.append_message(
            message={"role": "system", "content": agent.system_message},
            sender_type=EntityType.AGENT,
            sender_name=agent.name
        )
    # Optionally (but not strictly necessary): warm-start chat_history from disk
    agent.chat_history = agent.history_manager.load_chat_history(agent.name)
    if len(agent.chat_history) > 1:
        print("[Info] Previous history loaded for SoloAgent.\n")

    print('Type your messages! "show" displays chat history, "exit" to quit.')

    while True:
        msg = input("\nYou: ").strip()
        if msg.lower() == "exit":
            print("Session ended.")
            break
        elif msg.lower() == "show":
            print("=== Agent Chat History ===")
            for m in agent.chat_history:
                print(f"{m['role']}: {m['content']}")
            continue
        try:
            answer = agent.chat(msg)
            print("Agent:", answer)
        except Exception as e:
            print("Error:", e)

    print(f"\nHistory is now saved in nexus_workflows/{WORKFLOW_ID}/history.jsonl")

if __name__ == "__main__":
    main()