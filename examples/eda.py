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

import uuid

active_sessions = {}


def execute_command(argument: str):
    try:
        command = argument

        # Check if there's an available session
        if active_sessions:
            session_name = next(iter(active_sessions))
        else:
            # Generate a unique session name if no sessions are available
            session_name = f"session_{uuid.uuid4().hex[:8]}"
            active_sessions[session_name] = True

            # Create a new detached tmux session
            subprocess.run(["tmux", "new-session", "-d", "-s", session_name])

            # Open a new terminal window and attach it to the tmux session
            # Replace 'gnome-terminal' with 'xterm' or another terminal emulator if needed
            subprocess.Popen(["gnome-terminal", "--", "tmux", "attach-session", "-t", session_name])

        # Send the command to the tmux session
        subprocess.run(["tmux", "send-keys", "-t", session_name, "clear", "Enter"])  # Clear the screen first
        subprocess.run(["tmux", "send-keys", "-t", session_name, command, "Enter"])

        # Wait for the command to finish (you might need to adjust this)
        time.sleep(2)

        # Capture the output
        result = subprocess.run(["tmux", "capture-pane", "-t", session_name, "-p", "-S", "-1000", "-J"],
                                stdout=subprocess.PIPE,
                                text=True)
        output = result.stdout.strip()

        return {"status": "success", "output": output, "session": session_name}
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
    "You are a professional Verilog RTL planner. When users request Verilog code, your task is to create an initial plan for writing the code. Never assume details and always ask for complete information if anything is unclear or missing.",
    llm_config=llm_config)

coder = Agent(
    name="Coder",
    system_message=
    "You are a professional Verilog programmer. Always request complete information if anything is unclear or missing. Your task is to write Verilog code along with its corresponding testbench. The testbench must include instructions to generate a waveform.vcd file for visualization in GTKWave. Ensure your code is complete, functional, and adheres to Verilog best practices.",
    llm_config=llm_config)

debugger = Agent(
    name="Debugger",
    system_message=
    """You are a professional debugger and programmer specializing in Verilog. Always request complete information if anything is unclear or missing. You can access the terminal to run iverilog for testing code syntax and functionality, but you cannot generate code independently—always ask for the necessary code as input.

If you need to create files and execute iverilog, first ensure the ./verification_agent_env folder exists (create it if necessary). When writing code, always place the main Verilog code in top.v and the testbench in tb.v.

When asked to check syntax or functionality, ensure the testbench is provided. If not, create an appropriate testbench that generates a waveform.vcd file for visualization. You must follow these file naming conventions to proceed with the process. Lastly open gtkwave to visualize using: `gtkwave -S verification_agent_env/signals.tcl verification_agent_env/waveform.vcd`""",
    llm_config=llm_config,
    tools=tools)

# Initialize supervisor
supervisor = Orchestrator(name="supervisor", llm_config=llm_config)
supervisor.system_message = (
    """Think of yourself as a hardware design center manager overseeing other agents. When a user requests Verilog code, follow this process:
1. First, consult the planner agent to create an initial plan for writing the code.
2. Then, assign the task to the coder agent to write the Verilog code based on the plan.
3. Once the coder returns the Verilog code, you will send it to the Debugger agent to check its syntax and functionality using `iverilog`.
4. Ensure that the Debugger agent receives the code from the coder agent for validation.""" + supervisor.system_message)

supervisor.register_agent(planner)
supervisor.register_agent(coder)
supervisor.register_agent(debugger)


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
    to_ = message.get("to", "")

    if role == "user":
        container.chat_message("user", avatar="👦🏻").markdown(content)

    elif role == "orchestrator":
        if action == "output":
            container.chat_message("assistant", avatar="🤖").markdown(content)
        elif action == "thinking":
            container.chat_message("assistant",
                                   avatar="🧠").markdown(f"**Thinking about {to_[0].upper()+to_[1:]} Agent**\n\n{content}")
        else:
            container.chat_message("assistant", avatar="🤖").markdown(f"**{action.capitalize()}:**\n\n{content}")

    elif role == "coder":
        container.chat_message("assistant", avatar="💻").markdown(f"**Coder to Supervisor**\n```verilog\n{content}\n```")

    elif role == "planner":
        container.chat_message("assistant", avatar="📋").markdown(f"**Planner to Supervisor**\n\n{content}")

    elif role == "debugger":
        container.chat_message("assistant", avatar="🔍").markdown(f"**Debugger to Supervisor**\n\n{content}")

    else:
        container.chat_message("assistant").markdown(f"**{role.capitalize()}:**\n\n{content}")


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
    st.set_page_config(page_title="Chatbot with supervisor", layout="wide")
    st.markdown("""
    <style>
    .centered-title {
        text-align: center;
    }
    </style>
    """,
                unsafe_allow_html=True)

    st.markdown("<h2 class='centered-title'>NexusHDL</h2>", unsafe_allow_html=True)

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
            st.chat_message("user", avatar="👦🏻").markdown(user_input)
            placeholder = st.empty()
            with placeholder.container():
                st.spinner("Thinking...")
        # Call the supervisor in a separate thread
        thread = threading.Thread(target=supervisor.talk, args=(user_input,))
        thread.start()

        # Continuously check for new messages
        start_time = time.time()
        while time.time() - start_time < 30:  # Set a timeout (e.g., 30 seconds)
            if update_chat(chat_container):
                start_time = time.time()  # Reset the timeout if new messages are received

            # Check if the last message is from the supervisor with action "output"
            if (st.session_state.messages and st.session_state.messages[-1]["role"] == "supervisor" and
                    st.session_state.messages[-1].get("action") == "output"):
                break

            time.sleep(2)  # Short delay to prevent excessive checking

        # Wait for the supervisor thread to complete
        thread.join()

        # Final update to ensure all messages are displayed
        update_chat(chat_container)

    # Force a rerun to ensure all messages are displayed correctly
    st.rerun()


if __name__ == "__main__":
    main()
