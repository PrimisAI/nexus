import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primisai.nexus.architect import Architect

load_dotenv()

llm_config = {'model': os.getenv('LLM_MODEL'), 'api_key': os.getenv('LLM_API_KEY'), 'base_url': os.getenv('LLM_BASE_URL')}

user_query = """Design a workflow to solve GRE/SAT-style riddle questions and math problems. Use 1 supervisor and 1 Question Ansering Agent"""

"""JSON object containing the keys "question" and "answer".
Example line: {"question": "What is 2+2?", "answer": "4"}"""

benchmark_path = "path_to_the_data.jsonl"

architect = Architect(user_query=user_query,
                      benchmark_path=benchmark_path,
                      llm_config=llm_config,
                      workflow_name="math_riddle_solver",
                      subset_size=5,
                      max_iterations=2)

results = architect.build_and_optimize()

# --- 3. Review the Results ---
print("\n\n" + "=" * 25 + " FINAL SUMMARY " + "=" * 25)
print(f"✅ Process Completed!")
print(f"Final Accuracy: {results['final_accuracy']:.2%}")
print(f"Final optimized workflow file saved to: {results['output_path']}")
print("\n--- Performance History ---")
for record in results['history']:
    print(f"  - Iteration {record['iteration']}: Accuracy={record['accuracy']:.2%}, Saved to -> {record['saved_path']}")
print("=" * 67)
