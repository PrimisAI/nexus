# Orchestrator

This project is a Streamlit-based chatbot interface for a Hardware Design Orchestrator. It uses AI agents to assist with planning, coding, and debugging Verilog designs.

## Prerequisites

- Python 3.10+
- pip (Python package installer)

## Environment Setup

1. Create a `.env` file in the root directory of the project.
2. Add the following environment variables to the `.env` file:
   

      LLM_MODEL=your_model_name
      
      LLM_API_KEY=your_api_key
      
      LLM_BASE_URL=your_base_url

4. Replace `your_model_name`, `your_api_key`, and `your_base_url` with your actual LLM configuration values.

Note: The `.env` file contains sensitive information. Make sure to add it to your `.gitignore` file to prevent it from being committed to version control.

## Installation

1. Clone this repository
2. Install the required packages:

         pip install -r requirements.txt

## Running the Application

To run the Streamlit app, use the following command:

         streamlit run examples/eda.py
