from primisai.nexus.core import AI
from typing import Dict, Any


class WorkflowExpander:

    def __init__(self, llm_config: Dict[str, str]):
        """
        Initialize WorkflowExpander with LLM configuration.

        Args:
            llm_config: Dictionary containing LLM configuration
                        (api_key, model, base_url)
        """
        self.ai = AI(llm_config)

    def expand_workflow_query(self, user_query: str, nexus_guidelines: str) -> str:
        """
        Expand a high-level workflow query into detailed component pseudocode.

        Args:
            user_query: User's high-level workflow description
            nexus_guidelines: Basic guidelines about Nexus framework

        Returns:
            str: Expanded workflow description as structured pseudocode
        """
        # Construct the prompt
        messages = [{
            "role":
                "system",
            "content": (
                "You are an advanced workflow architect specializing in designing intelligent, modular, and efficient workflows using the Nexus framework. "
                "Your job is to deeply analyze high-level workflow requests and decompose them into a clear, structured set of components, strictly following the Nexus guidelines. "
                "For each workflow, identify the absolute minimum set of agents, supervisors, and tools required, ensuring no unnecessary complexity. "
                "For every component, clearly define its purpose, responsibilities, and how it interacts with other components. "
                "Always create output schemas that are tailored to the nature of the task—if the task requires logic or reasoning, design the schema accordingly. "
                "IMPORTANT: When passing the user query to agents, use the exact original wording without any modification. "
                "Do not provide implementation code—focus on architecture, structure, and clarity. "
                "Be precise, concise, and ensure your output is easy to follow for both humans and machines. "
                "DONT USE TOOLS UNTILL UNLESS NEEDED")
        }, {
            "role":
                "user",
            "content": (f"Nexus Framework Guidelines:\n{nexus_guidelines}\n\n"
                        f"User Query Request: {user_query}\n\n"
                        "Please provide a detailed description of the workflow components needed, "
                        "including supervisors, agents, and tools. Focus on their roles and responsibilities.")
        }]

        # Get response from LLM
        try:
            response = self.ai.generate_response(messages)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error in workflow expansion: {str(e)}")
