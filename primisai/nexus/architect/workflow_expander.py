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
        Expand a high-level workflow query into detailed component descriptions.
        
        Args:
            user_query: User's high-level workflow description
            nexus_guidelines: Basic guidelines about Nexus framework
            
        Returns:
            str: Expanded workflow description with components
        """
        # Construct the prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a workflow designer expert. Your task is to take a high-level "
                    "workflow request and create a detailed description of required components "
                    "based on the Nexus framework guidelines. Focus on describing what each "
                    "component should do rather than implementation details."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Nexus Framework Guidelines:\n{nexus_guidelines}\n\n"
                    f"User Query: {user_query}\n\n"
                    "Please provide a detailed description of the workflow components needed, "
                    "including supervisors, agents, and tools. Focus on their roles and responsibilities."
                )
            }
        ]

        # Get response from LLM
        try:
            response = self.ai.generate_response(messages)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error in workflow expansion: {str(e)}")

