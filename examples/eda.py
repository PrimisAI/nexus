import streamlit as st
import sys
import os
from dotenv import load_dotenv
import time
import subprocess
import json
import streamlit as st
import sys
import os
from dotenv import load_dotenv
import time
import subprocess
import json
from datetime import datetime
import streamlit as st
import json
import time
import os
import threading

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nexus.core import Agent, Orchestrator

llm_config = {'model': os.getenv('LLM_MODEL'), 'api_key': os.getenv('LLM_API_KEY'), 'base_url': os.getenv('LLM_BASE_URL')}

# def execute_command(argument: str):
#     try:

#         result = subprocess.run(argument, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         output = result.stdout + result.stderr
#         if result.returncode == 0:
#             return {"status": "success", "output": output.strip()}
#         else:
#             return {"status": "error", "output": output.strip()}
#     except Exception as e:
#         return {"status": "error", "output": str(e)}

# function_metadata = {
#     "type": "function",
#     "function": {
#         "name":
#             "execute_command",
#         "description":
#             "Execute a command on the Ubuntu terminal and capture the output or error. This function is called when user wants to execute any command on terminal",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "argument": {
#                     "type": "string",
#                     "description": "Command to execute on the Ubuntu terminal."
#                 }
#             },
#             "required": ["argument"]
#         }
#     }
# }

# tools = [{"tool": execute_command, "metadata": function_metadata}]

# # Initialize agents
# planner = Agent(
#     name="Planner",
#     system_message=
#     "You are a professional Verilog test planner who writes test plans when users ask for code. Don't assume; ask for complete information if it's missing.",
#     llm_config=llm_config)

# coder = Agent(
#     name="Coder",
#     system_message="You are a professional Verilog programmer. Don't assume; ask for complete information if it's missing.",
#     llm_config=llm_config)

# debugger = Agent(
#     name="Debugger",
#     system_message=
#     "You are a professional debugger programmer. Don't assume; ask for complete information if it's missing. You can access terminal to run iverilog to test code syntax and functionality. You cannot write code from your own. You should ask for code as input",
#     llm_config=llm_config,
#     tools=tools)

# # Initialize orchestrator
# orchestrator = Orchestrator(name="Orchestrator", llm_config=llm_config)
# orchestrator.system_message = ("Think you are a hardware design center manager who controls other agents. " +
#                                orchestrator.system_message)

# orchestrator.register_agent(planner)
# orchestrator.register_agent(coder)
# orchestrator.register_agent(debugger)

# orchestrator.talk(message="Here will be user message")


def execute_command(argument: str):
    try:
        result = subprocess.run(argument, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return {"status": "success", "output": output.strip()}
        else:
            return {"status": "error", "output": output.strip()}
    except Exception as e:
        return {"status": "error", "output": str(e)}


function_metadata = {
    "type": "function",
    "function": {
        "name":
            "execute_command",
        "description":
            "Execute a command on the Ubuntu terminal and capture the output or error. This function is called when user wants to execute any command on terminal",
        "parameters": {
            "type": "object",
            "properties": {
                "argument": {
                    "type": "string",
                    "description": "Command to execute on the Ubuntu terminal."
                }
            },
            "required": ["argument"]
        }
    }
}

tools = [{"tool": execute_command, "metadata": function_metadata}]

# Initialize agents
planner = Agent(
    name="Planner",
    system_message=
    "You are a professional Verilog test planner who writes test plans when users ask for code. Don't assume; ask for complete information if it's missing.",
    llm_config=llm_config)

coder = Agent(
    name="Coder",
    system_message="You are a professional Verilog programmer. Don't assume; ask for complete information if it's missing.",
    llm_config=llm_config)

debugger = Agent(
    name="Debugger",
    system_message=
    "You are a professional debugger programmer. Don't assume; ask for complete information if it's missing. You can access terminal to run iverilog to test code syntax and functionality. You cannot write code from your own. You should ask for code as input",
    llm_config=llm_config,
    tools=tools)

# Initialize orchestrator
orchestrator = Orchestrator(name="Orchestrator", llm_config=llm_config)
orchestrator.system_message = ("Think you are a hardware design center manager who controls other agents. " +
                               orchestrator.system_message)

orchestrator.register_agent(planner)
orchestrator.register_agent(coder)
orchestrator.register_agent(debugger)


def read_new_lines(file_path, last_position):
    messages = []
    current_position = last_position
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            file.seek(last_position)
            for line in file:
                try:
                    message = json.loads(line.strip())
                    messages.append(message)
                except json.JSONDecodeError:
                    pass  # Skip invalid JSON lines
            current_position = file.tell()
    return messages, current_position


def display_message(message, container):
    role = message["role"]
    action = message.get("action", "")
    content = message["content"]

    if role == "user":
        container.chat_message("user").markdown(content)
    elif role == "orchestrator":
        if action == "output":
            container.chat_message("assistant").markdown(content)
        else:
            with container.expander(f"Orchestrator - {action.capitalize()}", expanded=False):
                if action == "thinking":
                    st.info(content)
                elif action == "input":
                    st.success(content)
    elif role == "coder":
        with container.expander("Coder Output", expanded=False):
            st.code(content)
    else:
        with container.expander(f"{role.capitalize()}", expanded=False):
            st.write(content)


def update_chat(chat_container):
    new_messages, new_position = read_new_lines("chat.jsonl", st.session_state.file_position)
    if new_messages:
        st.session_state.messages.extend(new_messages)
        st.session_state.file_position = new_position

        # Update the UI with new messages
        for message in new_messages:
            display_message(message, chat_container)

    return len(new_messages) > 0


def main():
    st.set_page_config(page_title="Chatbot with Orchestrator", layout="wide")
    st.title("Chatbot with Orchestrator")

    # Initialize chat history and file position
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "file_position" not in st.session_state:
        st.session_state.file_position = 0

    # Create a container for the entire chat history
    chat_container = st.container()

    # Display existing chat history
    with chat_container:
        for message in st.session_state.messages:
            display_message(message, st)

    # Chat input
    user_input = st.chat_input("Your message:")

    if user_input:
        # Add user message to chat history and display immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            st.chat_message("user").markdown(user_input)

        # Call the orchestrator in a separate thread
        thread = threading.Thread(target=orchestrator.talk, args=(user_input,))
        thread.start()

        # Continuously check for new messages
        start_time = time.time()
        while time.time() - start_time < 30:  # Set a timeout (e.g., 30 seconds)
            if update_chat(chat_container):
                start_time = time.time()  # Reset the timeout if new messages are received

            # Check if the last message is from the orchestrator with action "output"
            if (st.session_state.messages and st.session_state.messages[-1]["role"] == "orchestrator" and
                    st.session_state.messages[-1].get("action") == "output"):
                break

            time.sleep(2)  # Short delay to prevent excessive checking

        # Wait for the orchestrator thread to complete
        thread.join()

        # Final update to ensure all messages are displayed
        update_chat(chat_container)

    # Force a rerun to ensure all messages are displayed correctly
    st.rerun()


if __name__ == "__main__":
    main()
