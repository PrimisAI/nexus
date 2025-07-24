from primisai.nexus.core import AI
from typing import Dict, Any



class WorkflowExpander:
    """
    Analyzes a user's initial query and expands it into a detailed, narrative plan.

    This class serves as the first step in the "Archtect" workflow creation
    pipeline. It takes a concise, high-level user request and uses a Large
    Language Model (LLM) to flesh it out into a comprehensive description.

    The primary goal of the expansion is to reason about the user's intent and
    propose a concrete plan. This includes identifying the individual tasks,
    determining the number and roles of AI agents required (e.g., a researcher,
    a writer), and deciding if a "supervisor" agent is needed to manage the
    overall workflow.

    The output of this class is a rich, natural-language text that serves as a
    more detailed "expanded prompt" for the next component in the system, the
    `WorkflowStructurer`.
    """

    def __init__(self, llm_config: Dict[str, str]):
        """
        Initializes the WorkflowExpander with LLM configuration.

        This constructor sets up the connection to the Large Language Model (LLM)
        that will be used to perform the query expansion and analysis.

        Args:
            llm_config (Dict[str, str]): A dictionary containing the configuration
                for the Language Model client. This typically includes essential
                details like 'api_key', 'model', and 'base_url'.
        """
        self.ai = AI(llm_config)

    def decompose_and_plan_tasks(self, user_query: str, nexus_guidelines: str) -> str:
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
                "You are an advanced workflow architect specializing in designing intelligent, modular, and efficient workflows using the Nexus framework."
                "Your job is to deeply analyze high-level workflow requests and decompose them into a clear, structured set of components, strictly following the Nexus guidelines."
                "For each workflow, identify the absolute minimum set of agents, supervisors, and tools required, ensuring no unnecessary complexity."
                "IMPORTANT: When passing the user query to agents, use the exact original wording without any modification. "
                "Do not provide implementation code—focus on architecture, structure, and clarity. "
                "Be precise, concise, and ensure your output is easy to follow for both humans and machines."
                "DONT USE TOOLS UNTILL UNLESS NEEDED. DONT USE Sub supervisors. Only supervisor and agents. Dont Use any output Schemas for Agents. Supervisor Cannot ask any feedback quetion from user"
            )
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
