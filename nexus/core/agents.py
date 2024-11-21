import openai, json
from typing import List, Dict, Optional
from nexus.core.ai import AI
from nexus.utils.debugger import Debugger


class Agent(AI):

    def __init__(self, name: str, llm_config: Dict[str, str], tools: Optional[List[Dict]] = None, system_message=None):
        super().__init__(llm_config=llm_config)
        self.name = name
        self.llm_config = llm_config
        self.tools = tools or []
        self.tools_metadata = []
        self.tools_metadata.extend([tool['metadata'] for tool in self.tools])
        self.system_message = system_message
        self.debugger = Debugger(name=name)
        self.debugger.start_session()
        # self.client = openai.OpenAI(base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
        #                             api_key=llm_config['api_key'])
        self.chat_history = []
        self.set_system_message(self.system_message)

    def set_system_message(self, message: str):
        """Set the system message for the agent."""
        self.chat_history.append({"role": "system", "content": message})

    def chat(self, task: str) -> Dict:
        self.debugger.log(f"Supervisor: {task}")
        self.chat_history.append({'role': 'user', 'content': task})

        while True:
            response = self.generate_response(self.chat_history, tools=self.tools_metadata, use_tools=True).choices[0]

            if response.finish_reason == "stop":
                user_query_answer = response.message.content
                self.debugger.log(f"{self.name}: {user_query_answer}")
                self.chat_history.append({"role": "assistant", "content": user_query_answer})
                return user_query_answer

            self.chat_history.append(response.message)
            function_call = response.message.tool_calls[0]
            target_tool_name = function_call.function.name
            tool_instruction = json.loads(function_call.function.arguments)['argument']

            target_tool = next((tool for tool in self.tools if tool['metadata']['function']['name'] == target_tool_name), None)

            if target_tool:
                tool_feedback = target_tool['tool'](tool_instruction)
                self.chat_history.append({"role": "tool", "content": str(tool_feedback), "tool_call_id": function_call.id})
