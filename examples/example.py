import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from nexus.ai import Agent, Orchestrator

llm_config = {'model': 'gpt-4o', 'api_key': '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'}

planner = Agent(name="Planner",
                system_message="You are professional verilog testplanner who write testplan when user ask for code",
                llm_config=llm_config)
coder = Agent(name="Coder", system_message="You are professional verilog programmer", llm_config=llm_config)
debugger = Agent(name="Debugger", system_message="You are professional debugger programmer", llm_config=llm_config)

orchestrator = Orchestrator(name="Ochestrator", llm_config=llm_config)
orchestrator.system_message = "Think you are a hardware design center manager who controls other agents. " + orchestrator.system_message

orchestrator.register_agent(planner)
orchestrator.register_agent(coder)
orchestrator.register_agent(debugger)

orchestrator.start_interactive_session()
