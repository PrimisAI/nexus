from primisai.nexus.core import AI
from typing import Dict
import json
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading
import time
import uuid


class Evaluator:
    """
    Evaluates the performance of generated agentic workflows against a benchmark.

    This class provides a framework for systematically testing the quality and
    correctness of workflows created by the "Archtect" system. It operates by
    running a generated workflow against a set of predefined tasks from a
    benchmark file.

    A key feature of this evaluator is its use of a Large Language Model (LLM)
    as a "judge" to score the output of the workflow. The LLM compares the
    workflow's final result against the ground-truth or expected outcome defined
    in the benchmark, providing a flexible and nuanced assessment of performance.
    """

    def __init__(self, llm_config: Dict[str, str], benchmark_path: str, subset_size: int = 10):
        """
        Initializes the Evaluator by loading the benchmark dataset.

        This constructor configures the LLM that will act as the evaluator and
        loads the benchmark problems from the specified JSONL file. It can also
        limit the evaluation to a smaller subset of the benchmark for faster testing.

        Args:
            llm_config (Dict[str, str]): The configuration for the Language Model
                that will be used as the AI judge for scoring the results.
            benchmark_path (str): The file path to the benchmark dataset. The file
                is expected to be in JSONL (JSON Lines) format, where each line
                is a JSON object representing a single test case.
            subset_size (int, optional): The number of examples to load from the
                benchmark file. If set, only the first `subset_size` examples
                will be used. Defaults to 10 for quick evaluations.

        Raises:
            FileNotFoundError: If the file at `benchmark_path` does not exist.
            ValueError: If `subset_size` is not a positive integer.
        """
        self.ai = AI(llm_config)
        self.benchmark_path = benchmark_path
        self.subset_size = subset_size
        self.benchmark_data = []
        self.test_subset = []
        self.results = []
        self.feed_chat_history = []
        # New attributes for tracking QA pairs and AI feedback
        self.all_qa_pairs = []
        self.failed_qa_pairs = []
        self.latest_ai_feedback = None
        self._results_lock = Lock()
        self._progress_lock = Lock()
        self.correct_answers = 0
        self.wrong_answers = 0
        # Load benchmark data
        self._load_benchmark()

    def _load_benchmark(self):
        """Load benchmark data and randomly select good quality examples."""
        try:
            with open(self.benchmark_path, 'r', encoding='utf-8') as file:
                for line in file:
                    data = json.loads(line.strip())
                    # Only keep good quality examples
                    # if data.get('quality', '').lower() == 'good':
                    self.benchmark_data.append(data)

            print(f"Loaded {len(self.benchmark_data)} examples from benchmark")

            # Randomly select subset_size examples instead of taking the first ones
            if len(self.benchmark_data) >= self.subset_size:
                self.test_subset = random.sample(self.benchmark_data, self.subset_size)
            else:
                self.test_subset = self.benchmark_data
                print(f"Warning: Only {len(self.benchmark_data)} examples available, using all")

        except Exception as e:
            raise Exception(f"Error loading benchmark: {str(e)}")

    def evaluate_supervisor(self, main_supervisor_or_factory, workflow_id, iteration, is_factory=False) -> Dict[str, Any]:
        """
        Evaluate the supervisor on the test subset with parallel processing.
        
        Args:
            main_supervisor_or_factory: Either a supervisor object or a factory function to create supervisors
            is_factory: If True, main_supervisor_or_factory is a factory function
            
        Returns:
            Dict: Evaluation results with scores and details
        """
        # Reset counters and results
        self.correct_answers = 0
        self.wrong_answers = 0
        self.results = []

        # Add thread-safe supervisor creation lock
        supervisor_creation_lock = threading.Lock()

        print(f"Testing supervisor on {len(self.test_subset)} examples...")

        # Initialize progress bar
        progress_bar = tqdm(total=len(self.test_subset), desc="Evaluating", unit="question")

        def process_example(example_with_index):
            i, example = example_with_index
            test_query = example['question']
            expected_answer = example['answer']

            try:
                # Create supervisor instance for this thread with thread-safe unique ID
                if is_factory:
                    with supervisor_creation_lock:  # Ensure thread-safe supervisor creation
                        # Create truly unique ID using UUID and thread ID

                        unique_suffix = f"{uuid.uuid4().hex[:8]}__{iteration}__{example.get('id', i)}__{i}"
                        supervisor = main_supervisor_or_factory(workflow_id, unique_suffix)
                else:
                    supervisor = main_supervisor_or_factory

                # Get response from supervisor
                response = supervisor.chat(test_query)
                path = "/home/humza/office/primisai/nexus/nexus_workflows/"
                path = path + workflow_id + "_" + str(unique_suffix)
                path = path + "/history.jsonl"
                messages = []
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            messages.append(json.loads(line))

                chat = """"""

                for i, msg in enumerate(messages):
                    if msg['role'] == "system":
                        continue

                    if msg['sender_type'] == "user":
                        if i == len(messages):
                            continue
                        else:
                            temp = "User to " + messages[i + 1]['sender_name'] + ": " + msg['content']
                            chat = chat + temp + "\n\n"

                    elif messages[i]['sender_type'] == "main_supervisor" and messages[i - 1]['sender_type'] == "main_supervisor":
                        content = msg['content']
                        to = messages[i - 1]['tool_calls'][0]['function']['name'].replace("delegate_to_", "")
                        from_ = msg['sender_name']
                        temp = from_ + " to " + to + " : " + content
                        chat = chat + temp + "\n\n"

                    elif msg['sender_type'] == "agent" and messages[i - 1]['sender_type'] == "main_supervisor":
                        content = msg['content']
                        to = messages[i - 1]['sender_name']
                        from_ = msg['sender_name']
                        temp = from_ + " to " + to + " : " + content
                        chat = chat + temp + "\n\n"

                    elif msg['sender_type'] == "main_supervisor" and msg['role'] == "assistant" and msg['content'] is not None:
                        content = msg['content']
                        to = "User"
                        from_ = msg['sender_name']
                        temp = from_ + " to " + to + " : " + content
                        chat = chat + temp + "\n\n"

                # Check answer correctness using LLM
                is_correct = self._check_answer_correctness(expected_answer, response)

                # Create result detail
                result_detail = {
                    'id': example.get('id', i),
                    'question': test_query,
                    'expected_answer': expected_answer,
                    'actual_response': response,
                    'is_correct': is_correct,
                    'difficulty': example.get('difficulty', 'unknown'),
                    'index': i,
                    'chat': chat
                }

                return result_detail, is_correct, None

            except Exception as e:
                result_detail = {
                    'id': example.get('id', i),
                    'question': test_query,
                    'expected_answer': expected_answer,
                    'actual_response': f"ERROR: {str(e)}",
                    'is_correct': False,
                    'difficulty': example.get('difficulty', 'unknown'),
                    'index': i
                }
                return result_detail, False, str(e)

        # Use parallel processing with multiple supervisor instances
        max_workers = min(8, len(self.test_subset))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {executor.submit(process_example, (i, example)): i for i, example in enumerate(self.test_subset)}

            # Process completed tasks as they finish
            for future in as_completed(future_to_index):
                try:
                    result_detail, is_correct, error = future.result()

                    # Thread-safe updates
                    with self._results_lock:
                        self.results.append(result_detail)
                        if is_correct:
                            self.correct_answers += 1
                        else:
                            self.wrong_answers += 1

                    # Thread-safe progress bar update
                    with self._progress_lock:
                        completed_count = len(self.results)
                        current_accuracy = self.correct_answers / self.subset_size if self.subset_size > 0 else 0
                        progress_bar.set_postfix({
                            'Accuracy': f"{current_accuracy:.2%}",
                            'Correct': self.correct_answers,
                            'Wrong': self.wrong_answers
                        })
                        progress_bar.update(1)

                except Exception as e:
                    print(f"Unexpected error processing example: {str(e)}")
                    with self._results_lock:
                        self.wrong_answers += 1
                    with self._progress_lock:
                        progress_bar.update(1)

        # Close progress bar
        progress_bar.close()

        # Sort results by original index to maintain order
        self.results.sort(key=lambda x: x['index'])

        # Remove the index field as it was only needed for sorting
        for result in self.results:
            del result['index']

        # Calculate final metrics
        total_examples = len(self.test_subset)
        accuracy = self.correct_answers / total_examples if total_examples > 0 else 0

        evaluation_results = {
            'total_examples': total_examples,
            'correct_answers': self.correct_answers,
            'wrong_answers': self.wrong_answers,
            'accuracy': accuracy,
            'error_rate': self.wrong_answers / total_examples if total_examples > 0 else 0,
            'detailed_results': self.results
        }

        print(f"\n=== Evaluation Results ===")
        print(f"Total Examples: {total_examples}")
        print(f"Correct Answers: {self.correct_answers}")
        print(f"Wrong Answers: {self.wrong_answers}")
        print(f"Final Accuracy: {accuracy:.2%}")
        print(f"Error Rate: {evaluation_results['error_rate']:.2%}")

        return evaluation_results

    def generate_feedback_summary(self, old_system_messages, evaluation_results: Dict[str, Any]) -> str:
        """
        Generate AI-powered structured feedback based on evaluation results and current system messages.
        
        Args:
            system_messages: Current workflow system messages for agents
            evaluation_results: Results from evaluate_supervisor()
            
        Returns:
            str: AI-generated feedback with detailed analysis
        """
        accuracy = evaluation_results['accuracy']
        detailed_results = evaluation_results['detailed_results']

        # Prepare all question-answer pairs for AI analysis
        qa_pairs = []
        failed_examples = []
        FAILED_METRIC = """Here are some examples from FAILED examples\n\n"""
        # Randomly select up to 10 failed examples to include in the feedback
        failed_results = [r for r in detailed_results if r['is_correct'] == False]
        # If there are more than 10 failed examples, select a random subset
        # Include all failed examples but only show chat for 10
        selected_for_chat = random.sample(failed_results, min(15, len(failed_results))) if len(failed_results) > 10 else failed_results
        chat_ids = [result['id'] for result in selected_for_chat]

        # Build the failed examples text
        for result in failed_results:
            example_text = f"{result['question']}\nExpected Answer: {result['expected_answer']}\nPredicted Answer: {result['actual_response']}\nIs Correct: {result['is_correct']}\n"

            # Only include chat for selected examples
            # if result['id'] in chat_ids:
            #     example_text += f"\nChat of this Example:\n{result['chat']}"

            FAILED_METRIC += example_text + "\n\n---\n\n"

        # Store in class attributes for future reference
        self.all_qa_pairs = qa_pairs
        self.failed_qa_pairs = failed_examples

        # Create comprehensive prompt for AI feedback generation
        system_message = {
            "role":
                "system",
            "content": (
                "You are an AI Workflow Performance Analyst specializing in identifying specific agent failures and providing precise system message improvements.\n"
                "\n"
                "YOUR ROLE:\n"
                "Analyze failed examples where AI agents couldn't solve questions correctly. You will receive:\n"
                "1. The original question\n"
                "2. Expected correct answer\n"
                "3. Actual predicted answer (wrong)\n"
                "4. Complete conversation/chat between AI agents trying to solve the question\n"
                "5. Current system message guidelines for each agent\n"
                "\n"
                "ANALYSIS PROCESS:\n"
                "1. Read the agent conversation carefully to identify WHERE the failure occurred\n"
                "2. Identify WHICH SPECIFIC AGENT made the critical error\n"
                "3. Compare the agent's behavior in the chat with their current system message guidelines\n"
                "4. Determine what guideline is missing, unclear, or causing the issue\n"
                "5. Provide exact system message modifications\n"
                "\n"
                "YOUR OUTPUT WILL BE USED BY:\n"
                "A prompt engineer who will directly update the agent system messages based on your recommendations.\n"
                "\n"
                "REQUIRED OUTPUT FORMAT (follow this exactly every time):\n"
                "\n"
                "# [EXACT_AGENT_NAME]\n"
                "Issue: [Describe what the agent did wrong based on the chat conversation]\n"
                "Root Cause: [What system message guideline is missing or inadequate]\n"
                "Chat Evidence: \"[Exact quote from agent's response in the conversation]\"\n"
                "Action Required: ADD/REMOVE/MODIFY\n"
                "Guideline Change: \"[Exact text to add, remove, or modify in the system message]\"\n"
                "\n"
                "# [ANOTHER_AGENT_NAME]\n"
                "NO CHANGE REQUIRED\n"
                "\n"
                "# [THIRD_AGENT_NAME]\n"
                "Issue: [Describe what the agent did wrong]\n"
                "Root Cause: [What system message guideline is missing]\n"
                "Chat Evidence: \"[Exact quote from agent's response]\"\n"
                "Action Required: ADD/REMOVE/MODIFY\n"
                "Guideline Change: \"[Exact text to add, remove, or modify]\"\n"
                "\n"
                "CRITICAL REQUIREMENTS:\n"
                "- Create one heading per agent (using exact agent names from the chat)\n"
                "- If an agent performed correctly or didn't cause issues, write 'NO CHANGE REQUIRED' under their heading\n"
                "- For agents with issues, provide all details under their single heading\n"
                "- Quote specific parts of the agent conversation as evidence\n"
                "- Provide actionable system message text that can be directly copy-pasted\n"
                "- Focus on guideline gaps, not just describing what went wrong\n"
                "- Each recommendation must be tied to specific chat evidence\n"
                "- Be precise about ADD/REMOVE/MODIFY actions for system messages\n"
                "\n"
                "Your analysis must be thorough but concise, focusing on the most critical system message improvements needed for each agent."
            )
        }

        # Prepare evaluation summary focusing on patterns not specifics
        evaluation_summary = f"""EVALUATION RESULTS SUMMARY:
    - Total Questions: {evaluation_results['total_examples']}
    - Correct Answers: {evaluation_results['correct_answers']}
    - Wrong Answers: {evaluation_results['wrong_answers']}
    - Accuracy: {accuracy:.2%}
    - Error Rate: {evaluation_results['error_rate']:.2%}
    """

        user_message = {
            "role":
                "user",
            "content":
                f"""CURRENT AGENT SYSTEM MESSAGES:
{old_system_messages}

## EVALUATION SUMMARY
{evaluation_summary}

## FAILED EXAMPLES WITH AGENT CONVERSATIONS
{FAILED_METRIC}

Please analyze each failed example by carefully reading the agent conversations. For each agent that participated:

1. Examine their specific responses and decisions in the chat
2. Identify which agents made critical errors that led to wrong answers
3. Compare their behavior against their current system message guidelines
4. Determine what specific guidelines are missing or inadequate
5. Provide exact system message modifications for each problematic agent

Focus on agent-specific issues revealed through their actual chat behavior. If an agent performed correctly and didn't contribute to the failure, indicate "NO CHANGE REQUIRED" for that agent.

Your analysis will be used to directly update individual agent system messages, so be precise about which agent needs what specific guideline changes."""
        }
        # if self.feed_chat_history == []:
        #     self.feed_chat_history.append(system_message)
        #     self.feed_chat_history.append(user_message)
        #     msgs = [system_message, user_message]
        # else:
        #     self.feed_chat_history.append(user_message)
        #     msgs = self._construct_messages_with_system_positioning(system_message)

        try:
            messages_ = [system_message, user_message]
            response = self.ai.generate_response(messages_)
            ai_feedback = response.choices[0].message.content
            self.feed_chat_history.append({'role': 'assistant', 'content': ai_feedback})
            # Store the AI feedback for reference
            self.latest_ai_feedback = ai_feedback

            return ai_feedback

        except Exception as e:
            print(f"Error generating AI feedback: {str(e)}")
            return self._generate_basic_feedback(evaluation_results)

    def _check_answer_correctness(self, actual: str, predicted: str) -> bool:
        """
        Check answer correctness using LLM evaluation with retry mechanism.
        
        Args:
            actual: The correct/expected answer
            predicted: The supervisor's predicted response
            
        Returns:
            bool: True if answers match, False otherwise
        """
        system_message = {
            "role":
                "system",
            "content":
                """You are an expert Reasoning and Analysis Agent. You will be given two answers: Actual (correct) vs Predicted (from AI system). 
Your task is to determine if both answers convey the same meaning or conclusion, even if worded differently.
PREDICTED ANSWER can be long and will have different explaination but you have to carefully analyze the meaning of the answer. See if Actual answer is found inside Predicted answer.
Actual Answer can be in Predicted answer but in different wording or explaination.

IMPORTANT: Reply with ONLY "1" or "0":
- 1 = Same meaning/conclusion (correct)
- 0 = Different meaning/conclusion (incorrect)

Consider:
- Semantic equivalence (same meaning, different words)
- Numerical accuracy for math problems  
- Logical consistency
- Core facts and conclusions"""
        }

        user_message = {
            "role":
                "user",
            "content":
                f"""Please analyze these two answers and determine if the Predicted Answer matches the Actual Answer in logic and reasoning.

Actual Answer: {actual}
Predicted Answer: {predicted}

Return ONLY: 1 (same) or 0 (different)"""
        }

        messages = [system_message, user_message]

        # Retry mechanism (up to 3 attempts)
        for attempt in range(3):
            try:
                response = self.ai.generate_response(messages)
                generated_content = response.choices[0].message.content.strip()

                # Extract digit from response using regex
                digit_match = re.search(r'\b([01])\b', generated_content)
                if digit_match:
                    result = digit_match.group(1)
                    return result == '1'  # Return True if 1, False if 0

                # If no clear 1 or 0 found, try again
                if attempt < 2:  # Don't print on last attempt
                    print(f"Warning: LLM evaluator returned unclear response: '{generated_content}'. Retrying...")

            except Exception as e:
                if attempt < 2:  # Don't print on last attempt
                    print(f"Error in LLM evaluation (attempt {attempt + 1}): {str(e)}. Retrying...")
                continue

        # If all attempts failed, fall back to simple string matching
        print("Warning: LLM evaluation failed after 3 attempts. Falling back to simple string matching.")
        return self._simple_string_matching(actual, predicted)

    def _simple_string_matching(self, actual: str, predicted: str) -> bool:
        """
        Fallback method for simple string matching.
        
        Args:
            actual: Expected answer
            predicted: Predicted answer
            
        Returns:
            bool: True if strings match (case-insensitive)
        """
        actual_clean = actual.lower().strip()
        predicted_clean = predicted.lower().strip()

        # Check if expected answer is contained in response or vice versa
        return (actual_clean in predicted_clean) or (predicted_clean in actual_clean)

    def _construct_messages_with_system_positioning(self, sys_msg) -> List[Dict[str, str]]:
        """
        Construct message list with system message positioned 2 places before the current message.
        
        Returns:
            List[Dict]: Properly positioned messages for API call
        """
        messages = []

        # If we have enough history, insert system message at correct position
        if len(self.feed_chat_history) >= 2:
            # Add all but last 2 messages
            messages.extend(self.feed_chat_history[:-2])
            # Add system message
            messages.append(sys_msg)
            # Add last 2 messages
            messages.extend(self.feed_chat_history[-2:])
        elif len(self.feed_chat_history) == 1:
            # Add system message, then the single history message
            messages.append(sys_msg)
            messages.extend(self.feed_chat_history)
        else:
            # No history yet, just system message
            messages.append(sys_msg)

        return messages
