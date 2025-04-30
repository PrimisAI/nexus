"""
Example demonstrating the Agent output schema functionality.
This example shows:
1. Basic schema usage
2. Strict vs non-strict mode
3. Different schema types (code, analysis, structured data)
4. Schema validation and reformatting
"""

import os, sys
import json
from pprint import pprint
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from primisai.nexus.core import Agent

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
        # Try to parse and pretty print as JSON
        parsed = json.loads(response)
        print("\nFormatted Response:")
        pprint(parsed, indent=2, width=80)
    except json.JSONDecodeError:
        # If not JSON, print as is
        print("\nPlain Response:")
        print(response)
    print("\n" + "="*50)

# Example 1: Code Generation Agent with Schema
code_schema = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Explanation of the code's purpose and functionality"
        },
        "code": {
            "type": "string",
            "description": "The actual code implementation"
        },
        "language": {
            "type": "string",
            "description": "Programming language used"
        }
    },
    "required": ["description", "code"]
}

code_agent = Agent(
    name="CodeWriter",
    llm_config=llm_config,
    system_message="You are a skilled programmer who writes clean, well-documented code.",
    output_schema=code_schema,
    strict=True  # Enforce JSON schema
)

# Example 2: Analysis Agent with Schema (non-strict)
analysis_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Brief summary of the analysis"
        },
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of key findings or points"
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of recommendations based on analysis"
        }
    },
    "required": ["summary", "key_points"]
}

analysis_agent = Agent(
    name="Analyst",
    llm_config=llm_config,
    system_message="You are an analytical expert who provides detailed insights.",
    output_schema=analysis_schema,
    strict=False  # Allow non-JSON responses if parsing fails
)

# Example 3: Regular Agent (no schema)
regular_agent = Agent(
    name="Assistant",
    llm_config=llm_config,
    system_message="You are a helpful assistant."
)

def test_code_agent():
    print("\n=== Testing Code Agent (Strict Schema) ===")
    query = "Write a Python function that calculates the factorial of a number."
    print(f"\nQuery: {query}")
    response = code_agent.chat(query)
    print_json_response(response, "Code Agent Response")

def test_analysis_agent():
    print("\n=== Testing Analysis Agent (Non-strict Schema) ===")
    query = "Analyze the advantages and disadvantages of remote work."
    print(f"\nQuery: {query}")
    response = analysis_agent.chat(query)
    print_json_response(response, "Analysis Agent Response")

def test_regular_agent():
    print("\n=== Testing Regular Agent (No Schema) ===")
    query = "What are the benefits of exercise?"
    print(f"\nQuery: {query}")
    response = regular_agent.chat(query)
    print_json_response(response, "Regular Agent Response")

def test_schema_enforcement():
    print("\n=== Testing Schema Enforcement ===")
    
    # Test 1: Complex query that might challenge schema compliance
    print("\nTest 1: Complex Query (Code Agent)")
    query = "Explain object-oriented programming and provide an example class."
    print(f"\nQuery: {query}")
    response = code_agent.chat(query)
    print_json_response(response, "Code Agent (Complex Query)")
    
    # Test 2: Query that might produce non-schema response
    print("\nTest 2: Potentially Non-Schema Response (Analysis Agent)")
    query = "Quick overview of climate change?"
    print(f"\nQuery: {query}")
    response = analysis_agent.chat(query)
    print_json_response(response, "Analysis Agent (Quick Overview)")

def display_schema_info():
    """Display the schemas being used in the example"""
    print("\n=== Schema Definitions ===")
    print("\nCode Agent Schema:")
    pprint(code_schema, indent=2, width=80)
    print("\nAnalysis Agent Schema:")
    pprint(analysis_schema, indent=2, width=80)
    print("\n" + "="*50)

def main():
    print("=== Output Schema Examples ===")
    print("This example demonstrates different ways to use output schemas with agents.")
    
    # Display schema definitions
    display_schema_info()
    
    # Test each agent type
    test_code_agent()
    test_analysis_agent()
    test_regular_agent()
    
    # Test schema enforcement
    test_schema_enforcement()

if __name__ == "__main__":
    main()