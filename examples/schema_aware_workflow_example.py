"""
Example demonstrating output schema functionality in a workflow with supervisor and agents.
This example simulates a software documentation workflow where:
1. A code analysis agent examines code (with structured output)
2. A documentation writer creates docs (with template schema)
3. A quality checker reviews (with checklist schema)
"""

import os, sys
import json
from pprint import pprint
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primisai.nexus.core import Agent, Supervisor

# Load environment variables
load_dotenv()

# LLM Configuration
llm_config = {
    'model': os.getenv('LLM_MODEL'),
    'api_key': os.getenv('LLM_API_KEY'),
    'base_url': os.getenv('LLM_BASE_URL')
}

def print_json_response(response: str, title: str = None):
    """Helper function to pretty print JSON responses"""
    if title:
        print(f"\n=== {title} ===")
    try:
        parsed = json.loads(response)
        print("\nFormatted Response:")
        pprint(parsed, indent=2, width=80)
    except json.JSONDecodeError:
        print("\nPlain Response:")
        print(response)
    print("\n" + "="*50)

# Define schemas for different agents
code_analyzer_schema = {
    "type": "object",
    "properties": {
        "complexity_score": {
            "type": "integer",
            "description": "Code complexity score (1-10)"
        },
        "key_components": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of main code components identified"
        },
        "potential_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of potential issues or improvements"
        }
    },
    "required": ["complexity_score", "key_components"]
}

doc_writer_schema = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Documentation title"
        },
        "overview": {
            "type": "string",
            "description": "Brief overview of the code/feature"
        },
        "usage_examples": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Example usage snippets"
        },
        "api_documentation": {
            "type": "object",
            "description": "API details",
            "properties": {
                "parameters": {"type": "array", "items": {"type": "string"}},
                "return_value": {"type": "string"}
            }
        }
    },
    "required": ["title", "overview", "usage_examples"]
}

quality_checker_schema = {
    "type": "object",
    "properties": {
        "passes_checklist": {
            "type": "boolean",
            "description": "Whether documentation passes all checks"
        },
        "checklist_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "comments": {"type": "string"}
                }
            }
        },
        "improvement_suggestions": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["passes_checklist", "checklist_results"]
}

# Create agents with schemas
code_analyzer = Agent(
    name="CodeAnalyzer",
    llm_config=llm_config,
    system_message="You are an expert code analyzer. Examine code and provide structured analysis.",
    output_schema=code_analyzer_schema,
    strict=True
)

doc_writer = Agent(
    name="DocWriter",
    llm_config=llm_config,
    system_message="You are a technical documentation writer. Create clear, comprehensive documentation.",
    output_schema=doc_writer_schema,
    strict=True
)

quality_checker = Agent(
    name="QualityChecker",
    llm_config=llm_config,
    system_message="You are a documentation quality checker. Ensure docs meet all standards.",
    output_schema=quality_checker_schema,
    strict=True
)

# Create and configure supervisor
doc_supervisor = Supervisor(
    name="DocSupervisor",
    llm_config=llm_config,
    system_message="""You are a documentation project supervisor. 
    Coordinate between the code analyzer, documentation writer, and quality checker.
    Follow this workflow:
    1. Have code analyzed first
    2. Based on analysis, request documentation
    3. Finally, check documentation quality"""
)

# Register agents
doc_supervisor.register_agent(code_analyzer)
doc_supervisor.register_agent(doc_writer)
doc_supervisor.register_agent(quality_checker)

def display_workflow_structure():
    """Display the workflow structure and schemas"""
    print("\n=== Workflow Structure ===")
    doc_supervisor.display_agent_graph()
    
    print("\n=== Agent Schemas ===")
    print("\nCode Analyzer Schema:")
    pprint(code_analyzer_schema)
    print("\nDoc Writer Schema:")
    pprint(doc_writer_schema)
    print("\nQuality Checker Schema:")
    pprint(quality_checker_schema)
    print("\n" + "="*50)

def test_documentation_workflow():
    """Test the complete documentation workflow"""
    # Test case: Python function documentation
    python_code = """
def calculate_fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
    """
    
    print("\n=== Testing Documentation Workflow ===")
    print("\nInput Code:")
    print(python_code)
    
    # First query: Request documentation for the code
    query = f"""Create documentation for this Python code:
    {python_code}
    
    Please analyze the code, create documentation, and verify quality."""
    
    print("\nInitial Query:", query)
    response = doc_supervisor.chat(query)
    print_json_response(response, "Supervisor's Final Response")
    
    # Follow-up query to demonstrate context awareness
    follow_up = "What were the main quality checks performed on this documentation?"
    print("\nFollow-up Query:", follow_up)
    response = doc_supervisor.chat(follow_up)
    print_json_response(response, "Supervisor's Follow-up Response")

def main():
    print("=== Documentation Workflow with Schema-Aware Agents ===")
    print("This example demonstrates a complete documentation workflow using")
    print("multiple agents with structured outputs managed by a supervisor.")
    
    # Display workflow structure and schemas
    display_workflow_structure()
    
    # Run the workflow test
    test_documentation_workflow()

if __name__ == "__main__":
    main()