import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from primisai.nexus.architect import (
    WorkflowExpander,
    WorkflowStructurer,
    WorkflowBuilder,
    prompts
)

load_dotenv()

llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

user_query = "Create a simple workflow for bedtime story generation."
test_query = "Create a bedtime story about a friendly star."

# Step 1: Expand the user query into detailed workflow components
expander = WorkflowExpander(llm_config)
try:
    expanded_workflow = expander.expand_workflow_query(user_query, prompts.nexus_guidelines)
    print("Expanded Workflow Description:")
    print(expanded_workflow)
except Exception as e:
    print(f"Error during expansion: {e}")
    exit(1)

# Step 2: Structure the expanded workflow into component definitions
structurer = WorkflowStructurer(llm_config)
try:
    structured_workflow = structurer.structure_workflow(expanded_workflow)
    print("\nStructured Workflow Components:")
    print(structured_workflow)
except Exception as e:
    print(f"Error during structuring: {e}")
    exit(1)

# Step 3: Build and validate the structured workflow
workflow_builder = WorkflowBuilder(structured_workflow, llm_config)
try:
    main_supervisor = workflow_builder.build_and_validate()

    # Optionally save workflow implementation
    workflow_builder.save_workflow_to_file('generated_workflow.py')

    print("\nGenerated Workflow Structure:")
    main_supervisor.display_agent_graph()
    print("\nTesting workflow with a sample query...")
    response = main_supervisor.chat(test_query)
    print(f"\nQuery: {test_query}")
    print(f"Response: {response}")
except Exception as e:
    print(f"Error in workflow building/testing: {str(e)}")
    raise