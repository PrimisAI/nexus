import sys, os, subprocess
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.core import Agent, Supervisor

load_dotenv()

llm_config = {
    'model': os.getenv('LLM_MODEL'), 
    'api_key': os.getenv('LLM_API_KEY'), 
    'base_url': os.getenv('LLM_BASE_URL')
    }

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
    "You are a professional debugger programmer. Don't assume; ask for complete information if it's missing. You can access terminal to run iverilog to test code syntax and functionality",
    llm_config=llm_config,
    tools=tools,
    use_tools=True)

# Initialize supervisor
supervisor = Supervisor(
    name="Supervisor", 
    system_message="Think you are a hardware design center manager who controls other agents.",
    llm_config=llm_config)

supervisor.register_agent(planner)
supervisor.register_agent(coder)
supervisor.register_agent(debugger)

supervisor.display_agent_graph()
supervisor.start_interactive_session()