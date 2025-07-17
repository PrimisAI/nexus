import os
from typing import Dict
from primisai.nexus.core import AI
from primisai.nexus.architect.schemas import WorkflowDefinition


class WorkflowStructurer:

    def __init__(self, llm_config: Dict[str, str]):
        """
        Initialize WorkflowStructurer with LLM configuration.
        
        Args:
            llm_config: Dictionary containing LLM configuration
        """
        self.llm_config = llm_config
        self.ai = AI(self.llm_config)

        curr_dir = os.path.dirname(os.path.abspath(__file__))
        doc_path = os.path.join(curr_dir, "NEXUS_DOCUMENTATION.md")

        with open(doc_path, "r", encoding="utf-8") as file:
            self.nexus_documentation = file.read()

    def structure_workflow(self, expanded_workflow: str) -> WorkflowDefinition:
        """
        Convert expanded workflow description into structured component definitions.
        
        Args:
            expanded_workflow: Detailed workflow description from previous step
            
        Returns:
            WorkflowDefinition: Structured workflow components
        """
        messages = [{
            "role":
                "system",
            "content": ("You are a workflow structure expert. Your task is to convert "
                        "the expanded workflow description into structured component "
                        "definitions following the provided schema. Include validation "
                        "constraints for each component. USE same system messages provided in query if provided. DONT change them")
        }, {
            "role":
                "system",
            "content": (f"Nexus Documentation:\n\n {self.nexus_documentation}"
                        "Based on the examples provided in the Nexus documentation, "
                        "please structure the expanded workflow description into "
                        "component definitions. Include supervisors, agents, and tools. "
                        "Also, add validation constraints for each component.")
        }, {
            "role":
                "user",
            "content": (
                f"Given the following workflow description:\n\n{expanded_workflow}\n\n"
                "Please provide structured definitions for all components including "
                "supervisors, agents, and tools. For tools, include both metadata "
                "and complete Python function implementations. Also include validation "
                "constraints for each component. Also try not to add whitespace in the "
                "names of components. Add a proper (detailed) system messgages for all the components. Detailing all the details. Covering all the points. USE same system messages provided in query. DONT change them"
            )
        }]

        try:
            completion = self.ai.client.beta.chat.completions.parse(messages=messages,
                                                                    response_format=WorkflowDefinition,
                                                                    model=self.llm_config["model"])
            return completion.choices[0].message.parsed
        except Exception as e:
            raise Exception(f"Error in workflow structuring: {str(e)}")
