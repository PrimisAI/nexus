import openai
import streamlit as st
import json
from dotenv import load_dotenv
from typing import List, Dict, Optional
from debugger import Debugger

load_dotenv()


class AI:

    def __init__(self, llm_config: Dict[str, str]):

        self.llm_config = llm_config
        self.client = openai.OpenAI(base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                                    api_key=llm_config['api_key'])

    def generate_response(self, messages: List[Dict[str, str]], tools: list, use_tools: bool = False) -> Dict:
        """
        Execute a chat completion.

        Args:
            messages (List[Dict[str, str]]): List of conversation messages.
            use_tools (bool): Whether to use function calling with tools.

        Returns:
            Dict: The response from the OpenAI API.
        """

        try:
            params = {
                "model": self.llm_config['model'],
                "messages": messages,
                "temperature": float(self.llm_config.get('temperature', 0.7))
            }

            if use_tools and tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            return {"error": f"Chat failed: {str(e)}"}


class Agent:

    def __init__(self, name: str, llm_config: Dict[str, str], tools: Optional[List[Dict]] = None, system_message=None):
        """
        Initialize an AI agent.

        Args:
            name (str): Name of the agent.
            llm_config (Dict[str, str]): Configuration for the language model.
            tools (Optional[List[Dict]]): List of tools for function calling.
        """
        self.name = name
        self.llm_config = llm_config
        self.tools = tools or []
        self.system_message = system_message
        self.debugger = Debugger(name=name)
        self.debugger.start_session()
        self.client = openai.OpenAI(base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                                    api_key=llm_config['api_key'])
        self.chat_history = []
        self.set_system_message(self.system_message)

    def set_system_message(self, message: str):
        """Set the system message for the agent."""
        self.chat_history.append({"role": "system", "content": message})

    def chat(self, task: str, use_tools: bool = False) -> Dict:
        """
        Execute a chat completion.

        Args:
            messages (List[Dict[str, str]]): List of conversation messages.
            use_tools (bool): Whether to use function calling with tools.

        Returns:
            Dict: The response from the OpenAI API.
        """
        self.chat_history.append({"role": "user", "content": task})
        self.debugger.log(f"Orchestrator: {task}")
        try:
            params = {
                "model": self.llm_config['model'],
                "messages": self.chat_history,
                "temperature": float(self.llm_config.get('temperature', 0.7))
            }

            if use_tools and self.tools:
                params["tools"] = self.tools
                params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**params)
            self.debugger.log(f"{self.name}: {response.choices[0].message.content}")
            return response
        except Exception as e:
            return {"error": f"Chat failed: {str(e)}"}


class Orchestrator(AI):

    def __init__(self, name: str, llm_config: Dict[str, str]):
        super().__init__(llm_config=llm_config)

        self.name = name
        self.system_message = 'You are a helpful user assistant. You can call agents one by one in sequence. Your task is to manage the agents named as:\n'
        self.registered_agents = []
        self.available_tools = []
        self.chat_history = []
        self.debugger = Debugger(name="orchestrator")
        self.debugger.start_session()

    def configure_system_prompt(self, system_prompt: str):
        self.system_message = {"role": "system", "content": system_prompt}

    def register_agent(self, agent: Agent):
        self.registered_agents.append(agent)

        self.available_tools.append({
            "type": "function",
            "function": {
                "name": f"delegate_to_{agent.name}",
                "description": agent.system_message,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_instruction": {
                            "type": "string",
                            "description": "Instruction to be sent to the selected agent by the Orchestrator"
                        }
                    },
                    "required": ["agent_instruction"]
                }
            }
        })

        self.system_message += f"{agent.name}: {agent.system_message}\n"

    def get_registered_agents(self) -> List[str]:
        return [agent.name for agent in self.registered_agents]

    def delegate_to_agent(self, orchestrator_response):
        function_call = orchestrator_response.message.tool_calls[0]
        target_agent_name = function_call.function.name.replace("delegate_to_", "").lower()
        agent_instruction = json.loads(function_call.function.arguments)['agent_instruction']

        self.debugger.log(f"Agent: {target_agent_name} | Instruction: {agent_instruction}")

        for agent in self.registered_agents:
            if agent.name.lower() == target_agent_name:
                agent_response = agent.chat(task=agent_instruction)
                self.debugger.log(f"{target_agent_name}: {agent_response.choices[0].message.content}")
                return agent_response.choices[0].message.content

        return f"Error: No agent found with name '{target_agent_name}'"

    def process_user_input(self, user_query: str):
        self.debugger.log(f"User: {user_query}")
        self.chat_history.append({'role': 'user', 'content': user_query})
        orchestrator_response = self.generate_response(self.chat_history, tools=self.available_tools, use_tools=True).choices[0]

        while True:
            if orchestrator_response.finish_reason != "stop":
                self.chat_history.append(orchestrator_response.message)
                agent_feedback = self.delegate_to_agent(orchestrator_response)
                self.chat_history.append({
                    "role": "tool",
                    "content": agent_feedback,
                    "tool_call_id": orchestrator_response.message.tool_calls[0].id
                })

                orchestrator_response = self.generate_response(self.chat_history, tools=self.available_tools,
                                                               use_tools=True).choices[0]

            else:
                user_query_answer = orchestrator_response.message.content
                self.debugger.log(f"Orchestrator: {user_query_answer}")
                self.chat_history.append({"role": "assistant", "content": user_query_answer})
                return user_query_answer

    def start_interactive_session(self):
        self.chat_history = [{'role': 'system', 'content': self.system_message}]
        while True:
            user_input = input("User: ")
            orchestrator_output = self.process_user_input(user_query=user_input)
            print(f"Orchestrator: {orchestrator_output}")
