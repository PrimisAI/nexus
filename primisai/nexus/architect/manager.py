import os
import datetime
import logging
from typing import Dict, Any, List, Optional

from primisai.nexus.architect.expander import WorkflowExpander
from primisai.nexus.architect.structurer import WorkflowStructurer
from primisai.nexus.architect.builder import WorkflowBuilder
from primisai.nexus.architect.prompter import Prompter
from primisai.nexus.architect.evaluator import Evaluator
from primisai.nexus.architect import prompts

# Configure logging for the library module
logger = logging.getLogger(__name__)


class Architect:
    """
    A high-level manager class to design, build, and optimize a multi-agent AI workflow.

    This class takes a user's high-level query and a JSONL dataset of
    question/answer pairs to iteratively generate and refine a Python-based
    multi-agent system. It orchestrates the Expander, Structurer, Prompter,
    Evaluator, and Builder components to produce an optimized workflow.
    """

    def __init__(self,
                 user_query: str,
                 benchmark_path: str,
                 llm_config: Dict[str, str],
                 output_dir: str = "./optimized_workflows",
                 workflow_name: str = "optimized_workflow",
                 subset_size: int = 10,
                 max_iterations: int = 5):
        """
        Initializes the Architect.

        Args:
            user_query (str): The high-level user requirement for the workflow.
            benchmark_path (str): The file path to the JSONL training data.
                                  
                                  IMPORTANT: Each line in this file must be a valid
                                  JSON object containing the keys "question" and "answer".
                                  
                                  Example line:
                                  {"question": "What is 2+2?", "answer": "4"}
                                  
            llm_config (Dict[str, str]): Configuration for the language model,
                                         e.g., {'model': '...', 'api_key': '...'}.
            output_dir (str): Directory to save the final workflow file and logs.
            workflow_name (str): The base name for the output Python file.
            subset_size (int): Number of samples from the benchmark to use for each evaluation.
            max_iterations (int): The maximum number of optimization loops to run.
        """
        # --- Validate Inputs ---
        if not os.path.exists(benchmark_path):
            raise FileNotFoundError(f"Benchmark file not found at: {benchmark_path}")
        if not all(k in llm_config for k in ['model', 'api_key']):
            raise ValueError("llm_config must contain 'model' and 'api_key'.")

        # --- Store Configuration ---
        self.user_query = user_query
        self.benchmark_path = benchmark_path
        self.llm_config = llm_config
        self.output_dir = output_dir
        self.workflow_name = workflow_name
        self.subset_size = subset_size
        self.max_iterations = max_iterations

        # --- Initialize Core Components ---
        logger.info("Initializing architect components...")
        self.expander = WorkflowExpander(self.llm_config)
        self.structurer = WorkflowStructurer(self.llm_config)
        self.evaluator = Evaluator(self.llm_config, self.benchmark_path, subset_size=self.subset_size)
        self.prompter: Optional[Prompter] = None  # Initialized after agents are known

        # --- Internal State ---
        self.structured_workflow = None
        self.system_messages: Dict[str, str] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.workflow_id = self._generate_workflow_id()

        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"WorkflowArchitect initialized. Output will be saved in '{self.output_dir}'.")

    def _generate_workflow_id(self) -> str:
        """Creates a unique identifier for this workflow build session."""
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y__%Hh-%Mmin")
        benchmark_name = os.path.splitext(os.path.basename(self.benchmark_path))[0]
        return f"{self.workflow_name}_subset={self.subset_size}_iter={self.max_iterations}_{benchmark_name}_{timestamp}"

    @staticmethod
    def _extract_system_messages(system_messages_obj: Any, agents_names: List[str]) -> Dict[str, str]:
        """
        Extracts system messages into a dictionary, handling both dict and Pydantic objects.
        """
        if isinstance(system_messages_obj, dict):
            return system_messages_obj

        system_messages_dict = {}
        for agent_name in agents_names:
            try:
                system_messages_dict[agent_name] = getattr(system_messages_obj, agent_name)
            except AttributeError:
                logger.warning(f"Could not get system message for agent '{agent_name}'. Using default.")
                system_messages_dict[agent_name] = "You are a helpful AI assistant."
        return system_messages_dict

    def _create_supervisor_instance(self, workflow_id: str, unique_suffix: int):
        """Factory function to create a supervisor instance for evaluation."""
        run_id = f"{workflow_id}_{unique_suffix}"
        builder = WorkflowBuilder(self.system_messages, self.structured_workflow, self.llm_config, run_id)
        return builder.build_component_and_validate()

    def _save_workflow_to_file(self, accuracy: float, iteration: int) -> str:
        """Builds the workflow with current system messages and saves it to a file."""
        accuracy_percent = f"{accuracy*100:.1f}"
        filename = f"{self.workflow_name}_iter_{iteration+1}_acc_{accuracy_percent}p.py"
        output_path = os.path.join(self.output_dir, filename)

        builder = WorkflowBuilder(self.system_messages, self.structured_workflow, self.llm_config, self.workflow_id)
        builder.build_component_and_validate()
        builder.save_workflow_to_file(output_path)
        logger.info(f"Workflow saved to: {output_path}")
        return output_path

    def build_and_optimize(self) -> Dict[str, Any]:
        """
        Executes the full workflow design and optimization process.

        Returns:
            Dict[str, Any]: A dictionary containing the final results, including
                            final accuracy, path to the saved file, and performance history.
        """
        logger.info("Step 1: Designing initial workflow from user query...")
        expanded_workflow = self.expander.decompose_and_plan_tasks(self.user_query, prompts.nexus_guidelines)
        self.structured_workflow = self.structurer.reasoning_workflow_design(expanded_workflow)

        agents_names = [self.structured_workflow.main_supervisor.name] + [agent.name for agent in self.structured_workflow.agents]
        logger.info(f"Created agents: {', '.join(agents_names)}")

        logger.info("Step 2: Generating initial system prompts for all agents...")
        self.prompter = Prompter(agents_names, self.llm_config)
        initial_messages_obj = self.prompter.generate_warmup_system_messages(self.user_query, self.structured_workflow)
        self.system_messages = self._extract_system_messages(initial_messages_obj, agents_names)

        logger.info(f"Step 3: Starting optimization loop for {self.max_iterations} iterations...")
        final_accuracy = 0.0
        output_path = ""

        for i in range(self.max_iterations):
            logger.info(f"\n{'='*20} Iteration {i+1}/{self.max_iterations} {'='*20}")

            logger.info("Evaluating current workflow performance...")
            evaluation_results = self.evaluator.evaluate_supervisor(self._create_supervisor_instance,
                                                                    self.workflow_id,
                                                                    iteration=i,
                                                                    is_factory=True)
            accuracy = evaluation_results['accuracy']
            final_accuracy = accuracy

            output_path = self._save_workflow_to_file(accuracy, i)

            self.performance_history.append({
                "iteration": i + 1,
                "accuracy": accuracy,
                "system_messages": self.system_messages.copy(),
                "saved_path": output_path
            })

            if accuracy >= 0.95 and i < self.max_iterations - 1:
                logger.info("Achieved >95% accuracy. Stopping optimization early.")
                break

            if i < self.max_iterations - 1:
                logger.info("Generating feedback for improvement...")
                feedback = self.evaluator.generate_feedback_summary(str(self.system_messages), evaluation_results)

                logger.info("Updating system messages based on feedback...")
                self.system_messages = self.prompter.update_system_messages_with_feedback(self.system_messages, accuracy, feedback)
            else:
                logger.info(f"Max iterations ({self.max_iterations}) reached.")

        logger.info("\nWorkflow optimization complete.")
        logger.info(f"Final Accuracy: {final_accuracy:.2%}")
        logger.info(f"Most recent workflow saved at: {output_path}")

        return {
            "final_accuracy": final_accuracy,
            "output_path": output_path,
            "history": self.performance_history,
        }
