from primisai.nexus.core import AI
from typing import Dict, Any, List
from copy import deepcopy
from pydantic import BaseModel, create_model


def process_system_messages(old_system_messages, new_system_messages):
    """
    Process system messages by:
    1. Removing agent names (first part before ':' in first 100 characters)
    2. Keeping old message if new message contains 'NO_CHANGE'
    """
    processed_messages = {}

    def clean_message(message):
        """Remove agent name prefix from message"""
        # Take first 100 characters to find the colon
        first_part = message[:100]
        colon_index = first_part.find(':')

        if colon_index != -1:
            # Remove everything before and including the colon, then strip whitespace
            cleaned = message[colon_index + 1:].strip()
            return cleaned
        else:
            # If no colon found in first 100 chars, return original message
            return message

    # Process each agent
    for agent_name in new_system_messages.keys():
        new_message = new_system_messages[agent_name]

        # Check if new message contains NO_CHANGE
        if 'NO_CHANGE' in new_message:
            # Use old message and clean it
            if agent_name in old_system_messages:
                processed_messages[agent_name] = clean_message(old_system_messages[agent_name])
            else:
                processed_messages[agent_name] = new_message  # fallback
        else:
            # Use new message and clean it
            processed_messages[agent_name] = clean_message(new_message)

    return processed_messages


def extract_system_messages(system_messages_obj, agents_names):
    """Extract system messages from either dict or Pydantic object"""
    if isinstance(system_messages_obj, dict):
        return system_messages_obj
    else:
        # Handle Pydantic object
        system_messages_dict = {}
        for agent_name in agents_names:
            try:
                system_messages_dict[agent_name] = getattr(system_messages_obj, agent_name)
            except AttributeError:
                print(f"Warning: Could not get system message for agent {agent_name}")
                system_messages_dict[agent_name] = "No system message available"
        return system_messages_dict


def create_dynamic_schema(agent_names):
    """
    Create a dynamic Pydantic model with fields for each agent name.
    
    Args:
        agent_names: List of agent names
        
    Returns:
        Dynamically created Pydantic model class
    """
    fields = {agent_name: (str, ...) for agent_name in agent_names}
    return create_model('ResponseStructure', **fields)


class Prompter:
    """
    A specialized class for crafting and managing prompts for AI agents.

    Within a multi-agent framework, this class acts as a central prompt
    engineering hub. It is responsible for creating contextually-aware and
    role-specific prompts that guide each agent's behavior and responses.

    By encapsulating prompt logic here, we can easily manage system messages,
    task instructions, and the formatting of conversational history to ensure
    agents perform their designated functions effectively.
    """

    def __init__(self, agent_names: List[str], llm_config: Dict[str, str]):
        """
        Initializes the Prompter instance.

        This constructor sets up the prompter with the names of the agents it will
        be generating prompts for, and the configuration for the Language Model
        that might be used in the prompting process.

        Args:
            agent_names (List[str]): A list of unique string identifiers for the
                AI agents in the system. This allows the prompter to tailor
                instructions for specific agent roles.
            llm_config (Dict[str, str]): A dictionary containing the configuration
                for the Language Model client. It typically includes essential
                keys like 'api_key', 'model', and 'base_url'.
        """
        self.ai = AI(llm_config)
        self.model = llm_config.get("model", "gpt-4.1")
        self.conversation_history = []  # Store all messages in conversation
        self.agent_names = agent_names  # List of agent names for system messages
        self.system_message = {
            "role":
                "system",
            "content": (
                "You are an AI Prompt Engineer specializing in updating system messages for AI agents based on performance feedback analysis.\n"
                "\n"
                "YOUR ROLE:\n"
                "You receive detailed feedback from a Performance Analyst who has identified specific agent failures by analyzing failed examples and agent conversations. Your job is to implement precise system message updates to fix these identified issues.\n"
                "\n"
                "INPUT YOU RECEIVE:\n"
                "1. Current system messages for all agents\n"
                "2. Structured feedback in format:\n"
                "   # [AGENT_NAME]\n"
                "   Issue: [what went wrong]\n"
                "   Root Cause: [missing/inadequate guideline]\n"
                "   Chat Evidence: [quote from agent conversation]\n"
                "   Action Required: ADD/REMOVE/MODIFY\n"
                "   Guideline Change: [exact text to implement]\n"
                "\n"
                "YOUR SYSTEM MESSAGE UPDATE PROCESS:\n"
                "1. For each agent in the feedback, read their current system message\n"
                "2. Implement the EXACT changes specified in 'Action Required' and 'Guideline Change'\n"
                "3. If Action = ADD: Add the guideline text to appropriate section\n"
                "4. If Action = REMOVE: Remove the specified problematic text\n"
                "5. If Action = MODIFY: Replace old text with new guideline text\n"
                "6. Preserve all existing working guidelines unless explicitly told to remove them\n"
                "If needed try to add few shot example from feedback to enhance performance of Agent"
                "\n"
                "CRITICAL RULES:\n"
                "- NEVER remove or change the core agent identity (\"You are XYZ Agent...\")\n"
                "- Only modify what the feedback explicitly specifies\n"
                "- If feedback says 'NO CHANGE REQUIRED' for an agent, output: 'AGENT_NAME: NO_CHANGE'\n"
                "- Keep all other working system message parts intact\n"
                "- If Accuracy of current system messages is lesser than last one then get the last ones and update them based on feedback"
                "- Make surgical, targeted updates based on evidence-based feedback\n"
                "\n"
                "OUTPUT FORMAT (use exactly):\n"
                "AGENT_NAME: [complete updated system message]\n"
                "or\n"
                "AGENT_NAME: NO_CHANGE\n"
                "\n"
                "FORMATTING REQUIREMENTS:\n"
                "- DO NOT include agent names inside the system message content\n"
                "- Start system messages with 'You are...' directly\n"
                "- DO NOT add headers or prefixes within the message text\n"
                "- Maintain clean, professional system message structure\n"
                "\n"
                "VALIDATION CHECK:\n"
                "Before finalizing each update, verify:\n"
                "- Does this change address the specific issue identified in the chat evidence?\n"
                "- Have I preserved the agent's core identity and working capabilities?\n"
                "- Is the new guideline clear and actionable?\n"
                "\n"
                "Your updates will directly fix the reasoning failures identified through actual agent conversation analysis.")
        }

        self.current_system_messages = None
        self.ResponseStructure = create_dynamic_schema(agent_names)

    def generate_warmup_system_messages(self, user_query: str, workflow: str) -> str:
        """
        Generate initial system messages for workflow components.
        
        Args:
            workflow: Detailed workflow description
            
        Returns:
            str: Generated system messages for all components
        """
        # Create user message for initial generation

        system_message = {
            "role":
                "system",
            "content": (
                "You are an expert AI Prompt Engineer. Your task is to generate clear, effective system messages for each agent in a workflow, based on the provided User Query and workflow description.\n\n"
                "INSTRUCTIONS:\n"
                "- For each agent, write a system message that starts with 'You are...' and clearly defines the agent's role and responsibilities in the workflow.\n"
                "- Ensure each system message is actionable, unambiguous, and tailored to the agent's function.\n"
                "- Do not include agent names inside the message content; only use them as keys.\n"
                "- Avoid unnecessary headers or prefixes. Focus on clarity and completeness.\n"
                "- If possible, include a brief example of the agent's expected behavior.\n\n"
                "OUTPUT FORMAT:\n"
                "[complete system message for that agent]\n\n"
                "Begin by analyzing the User Query and workflow, then generate 1-2 line system messages for all supervisors and agents required to accomplish the workflow."
            )
        }

        user_message = {
            "role":
                "user",
            "content":
                f"""This is User Query on which workflow is generated\n\n{user_query}\n{workflow}.\n Generate all supervisor, agents name and their system messages """
        }

        # Add to conversation history
        # self.conversation_history.append(user_message)

        # Construct messages with system message at correct position
        # messages = self._construct_messages_with_system_positioning()
        messages = [system_message, user_message]

        # Get response from LLM
        try:

            generated_content = self.ai.client.beta.chat.completions.parse(messages=messages,
                                                                           response_format=self.ResponseStructure,
                                                                           model=self.model)

            # response = self.ai.generate_response(messages)
            # generated_content = response.choices[0].message.content

            # # Store the generated system messages
            # self.current_system_messages = generated_content

            # Add assistant response to conversation history
            assistant_message = {"role": "assistant", "content": str(generated_content.choices[0].message.parsed)}
            self.conversation_history.append(user_message)
            self.conversation_history.append(assistant_message)

            return generated_content.choices[0].message.parsed

        except Exception as e:
            raise Exception(f"Error in system message generation: {str(e)}")

    def update_system_messages_with_feedback(self, old_system_messages, accuracy, feedback: str) -> str:
        """
        Update system messages based on performance feedback.
        
        Args:
            feedback: Feedback containing issues and improvement suggestions
                     Expected format:
                     # POSSIBLE ISSUES
                     ...
                     # IMPROVEMENTS
                     ...
                     
        Returns:
            str: Updated system messages
        """

        # Create feedback message
        feedback_message = f'''CURRENT SYSTEM MESSAGES:
{old_system_messages}

Accuracy on these system messages: {accuracy}

PERFORMANCE ANALYST FEEDBACK:
{feedback}

IMPLEMENTATION INSTRUCTIONS:
1. Read the structured feedback for each agent carefully
2. For agents with "NO CHANGE REQUIRED" in feedback → Output: "AGENT_NAME: NO_CHANGE"
3. For agents with specific issues identified:
   - Implement the EXACT "Action Required" (ADD/REMOVE/MODIFY)
   - Keep all other existing system message intact
4. REDUNDANCY CHECK: If the "Guideline Change" already exists in current system message → Output: "AGENT_NAME: NO_CHANGE""""
OUTPUT FORMAT REQUIREMENTS:
- AGENT_NAME: NO_CHANGE (if no update needed)
- AGENT_NAME: [complete updated system message] (if update needed)
- DO NOT include explanations or analysis text
- DO NOT write agent names within the system message content

The feedback is based on actual agent conversation analysis - implement changes precisely to fix the identified reasoning failures.'''

        # Add to conversation history

        self.conversation_history.append({'role': 'user', 'content': feedback_message})

        # Construct messages with system message at correct position
        messages = self._construct_messages_with_system_positioning()

        # messages_ = [self.system_message, {'role': 'user', 'content': feedback_message}]

        # Get response from LLM
        try:

            response = self.ai.client.beta.chat.completions.parse(messages=messages,
                                                                  response_format=self.ResponseStructure,
                                                                  model=self.model)
            # response = self.ai.generate_response(messages)
            # updated_content = response.choices[0].message.content

            # Update stored system messages
            # self.current_system_messages = updated_content

            # Add assistant response to conversation history
            assistant_message = {"role": "assistant", "content": str(response.choices[0].message.parsed)}
            self.conversation_history.append(assistant_message)

            new_system_messages = extract_system_messages(response.choices[0].message.parsed, self.agent_names)
            result = process_system_messages(old_system_messages, new_system_messages)
            return result

        except Exception as e:
            raise Exception(f"Error in system message update: {str(e)}")

    def _construct_messages_with_system_positioning(self) -> List[Dict[str, str]]:
        """
        Construct message list with system message positioned 2 places before the current message.
        
        Returns:
            List[Dict]: Properly positioned messages for API call
        """
        messages = []

        # If we have enough history, insert system message at correct position
        if len(self.conversation_history) >= 2:
            # Add all but last 2 messages
            messages.extend(self.conversation_history[:-2])
            # Add system message
            messages.append(self.system_message)
            # Add last 2 messages
            messages.extend(self.conversation_history[-2:])
        elif len(self.conversation_history) == 1:
            # Add system message, then the single history message
            messages.append(self.system_message)
            messages.extend(self.conversation_history)
        else:
            # No history yet, just system message
            messages.append(self.system_message)

        return messages
        """
        Get a summary of the conversation state.
        
        Returns:
            Dict: Summary including message count, iterations, and current state
        """
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]

        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "iterations": len(assistant_messages),  # Each assistant response is an iteration
            "has_current_system_messages": self.current_system_messages is not None,
            "last_update": self.conversation_history[-1]["content"][:100] + "..." if self.conversation_history else None
        }
