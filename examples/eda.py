import streamlit as st
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nexus.core import Agent, Orchestrator

llm_config = {'model': os.getenv('LLM_MODEL'), 'api_key': os.getenv('LLM_API_KEY'), 'base_url': os.getenv('LLM_BASE_URL')}

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
    system_message="You are a professional debugger programmer. Don't assume; ask for complete information if it's missing.",
    llm_config=llm_config)

# Initialize orchestrator
orchestrator = Orchestrator(name="Orchestrator", llm_config=llm_config)
orchestrator.system_message = ("Think you are a hardware design center manager who controls other agents. " +
                               orchestrator.system_message)

orchestrator.register_agent(planner)
orchestrator.register_agent(coder)
orchestrator.register_agent(debugger)

orchestrator.start_interactive_session()

# # Streamlit App
# st.set_page_config(page_title="Hardware Design Orchestrator", page_icon="🖥️", layout="wide")

# st.title("🖥️ Hardware Design Orchestrator")

# # Orchestrator System Message Editor
# st.subheader("Orchestrator System Message")
# if "orchestrator_system_message" not in st.session_state:
#     st.session_state.orchestrator_system_message = orchestrator.system_message

# new_system_message = st.text_area("Edit the Orchestrator's system message:",
#                                   value=st.session_state.orchestrator_system_message,
#                                   height=100)

# if st.button("Update System Message"):
#     orchestrator.system_message = new_system_message
#     st.session_state.orchestrator_system_message = new_system_message
#     st.success("System message updated successfully!")

# st.write("---")

# st.write("Interact with the hardware design orchestrator and its agents (Planner, Coder, Debugger).")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Display chat messages
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # User input
# if prompt := st.chat_input("What can I help you with?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Orchestrator response
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
#         for response in orchestrator.process_user_input(user_query=prompt):
#             full_response += response
#             message_placeholder.markdown(full_response + "▌")
#         message_placeholder.markdown(full_response)
#     st.session_state.messages.append({"role": "assistant", "content": full_response})

# # Sidebar with agent information
# st.sidebar.title("Agents")
# st.sidebar.write("**Planner:** Verilog test planner")
# st.sidebar.write("**Coder:** Verilog programmer")
# st.sidebar.write("**Debugger:** Professional debugger")

# # Clear chat button
# if st.sidebar.button("Clear Chat"):
#     st.session_state.messages = []
