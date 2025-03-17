"""
This module provides functionality for managing conversation history in hierarchical
AI workflows. It handles storage and retrieval of messages between users,
supervisors, agents, and tools within a workflow.

The module uses a JSONL-based storage system where each workflow's conversation
history is stored in a dedicated file, supporting message threading, delegation
chains, and relationship tracking between different entities.

Components:
    EntityType: Enum for different entity types (USER, MAIN_SUPERVISOR, etc.)
    HistoryManager: Main class for handling history operations

Structure:
    nexus_workflows/{workflow_id}/history.jsonl

Note:
    Workflow directory must be initialized by a main supervisor before use.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum

class EntityType(str, Enum):
    """Enumeration of entity types in the workflow system."""
    USER = "user"
    MAIN_SUPERVISOR = "main_supervisor"
    ASSISTANT_SUPERVISOR = "assistant_supervisor"
    AGENT = "agent"
    TOOL = "tool"

class HistoryManager:
    """
    Manages conversation history for workflows involving supervisors, agents, and tools.
    
    This class works alongside the chat_history in Supervisor and Agent classes,
    providing persistent storage and advanced querying capabilities while maintaining
    the conversation structure and relationships.

    Attributes:
        workflow_id (str): Unique identifier for the workflow
        workflow_path (Path): Path to the workflow directory
        history_file (Path): Path to the JSONL file storing the conversation history
    """

    def __init__(self, workflow_id: str):
        """
        Initialize the HistoryManager.

        Args:
            workflow_id (str): Unique identifier for the workflow.
                             Must be provided by a main supervisor.

        Raises:
            ValueError: If workflow_id is None or workflow directory doesn't exist.
        """
        if not workflow_id:
            raise ValueError("workflow_id must be provided")

        self.workflow_id = workflow_id
        self.workflow_path = Path("nexus_workflows") / self.workflow_id
        self.history_file = self.workflow_path / "history.jsonl"

        if not self.workflow_path.exists():
            raise ValueError(
                f"Workflow directory does not exist: {self.workflow_path}. "
                "It should be created by the main supervisor."
            )

    def append_message(self,
                    message: Dict[str, Any],
                    sender_type: EntityType,
                    sender_name: str,
                    parent_id: Optional[str] = None,
                    tool_call_id: Optional[str] = None,
                    supervisor_chain: Optional[List[str]] = None) -> str:
        """
        Append a message to the conversation history.
        
        This method is called alongside chat_history updates to maintain
        persistent storage of the conversation.

        Args:
            message (Dict[str, Any]): The message to append (same format as chat_history)
            sender_type (EntityType): Type of the sender
            sender_name (str): Name of the sender
            parent_id (Optional[str]): ID of the parent message in conversation
            tool_call_id (Optional[str]): ID of related tool call if applicable
            supervisor_chain (Optional[List[str]]): List of supervisors in the delegation chain

        Returns:
            str: Generated message ID for reference in future messages

        Example:
            >>> msg_id = history_manager.append_message(
            ...     message={"role": "user", "content": "Hello"},
            ...     sender_type=EntityType.USER,
            ...     sender_name="user"
            ... )
            
            >>> msg_id = history_manager.append_message(
            ...     message={"role": "assistant", "content": "Process data"},
            ...     sender_type=EntityType.MAIN_SUPERVISOR,
            ...     sender_name="MainSupervisor",
            ...     supervisor_chain=["MainSupervisor", "AssistantSupervisor"]
            ... )
        """
        message_id = str(uuid.uuid4())
        
        # Prepare entry with metadata
        entry = {
            'message_id': message_id,
            'timestamp': datetime.utcnow().isoformat(),
            'workflow_id': self.workflow_id,
            'sender_type': sender_type,
            'sender_name': sender_name,
            'parent_id': parent_id,
            'tool_call_id': tool_call_id,
            'supervisor_chain': supervisor_chain or [],  # Empty list if None
            **message  # Include original message fields
        }

        # Append to history file
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return message_id

    def load_chat_history(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Load relevant chat history for an entity.

        This method is used when initializing or restoring an entity's state.
        It returns messages in a format compatible with chat_history.

        Args:
            entity_name (str): Name of the entity (supervisor or agent)

        Returns:
            List[Dict[str, Any]]: List of messages in chat_history format

        Example:
            >>> agent.chat_history = history_manager.load_chat_history("AgentName")
        """
        history = []
        if not self.history_file.exists():
            return history

        with open(self.history_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                if self._is_relevant_message(msg, entity_name):
                    history.append(self._format_for_chat_history(msg))

        return self._sort_messages(history)

    def get_frontend_history(self) -> List[Dict[str, Any]]:
        """
        Get complete conversation history formatted for frontend display.

        Returns:
            List[Dict[str, Any]]: Complete conversation history with proper threading

        Example:
            >>> history = history_manager.get_frontend_history()
        """
        if not self.history_file.exists():
            return []

        messages = []
        with open(self.history_file, 'r') as f:
            messages = [json.loads(line) for line in f]

        # Add delegation chain information for display
        for msg in messages:
            if msg.get('supervisor_chain'):
                msg['delegation_path'] = ' → '.join(msg['supervisor_chain'])
            
            # Format display name based on sender type and chain
            if msg['sender_type'] in [EntityType.MAIN_SUPERVISOR, EntityType.ASSISTANT_SUPERVISOR]:
                msg['display_name'] = f"{msg['sender_type']}: {msg['sender_name']}"
                if msg.get('supervisor_chain'):
                    msg['display_name'] += f" ({msg['delegation_path']})"
            else:
                msg['display_name'] = (
                    "User" if msg['sender_type'] == EntityType.USER else msg['sender_name']
                )

        return self._build_conversation_thread(messages)

    def _is_relevant_message(self, msg: Dict[str, Any], entity_name: str) -> bool:
        """
        Determine if a message is relevant for an entity's chat history.

        Args:
            msg (Dict[str, Any]): Message to check
            entity_name (str): Name of the entity

        Returns:
            bool: True if message is relevant for the entity
        """
        # Direct messages to/from the entity
        if msg['sender_name'] == entity_name:
            return True

        # Messages where entity is in the supervisor chain
        if entity_name in msg.get('supervisor_chain', []):
            return True

        # System messages
        if msg['role'] == 'system':
            return True
        
        # Messages that entity should see as delegated tasks
        if msg['role'] == 'user' and msg['sender_type'] in [
            EntityType.MAIN_SUPERVISOR,
            EntityType.ASSISTANT_SUPERVISOR
        ]:
            # Check tool calls for delegation
            if 'tool_calls' in msg:
                tool_call = msg.get('tool_calls', [{}])[0]
                if tool_call.get('function', {}).get('name', '').endswith(entity_name.lower()):
                    return True

        return False

    def _format_for_chat_history(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a message for use in chat_history.

        Args:
            msg (Dict[str, Any]): Raw message from storage

        Returns:
            Dict[str, Any]: Formatted message for chat_history
        """
        # Extract fields used in chat_history
        formatted = {
            'role': msg['role'],
            'content': msg['content']
        }

        # Include tool-specific fields if present
        if 'tool_calls' in msg:
            formatted['tool_calls'] = msg['tool_calls']
        if 'tool_call_id' in msg and msg['tool_call_id']:
            formatted['tool_call_id'] = msg['tool_call_id']

        return formatted

    def _sort_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort messages based on their relationships and timestamps.

        Args:
            messages (List[Dict[str, Any]]): Messages to sort

        Returns:
            List[Dict[str, Any]]: Sorted messages
        """
        return sorted(messages, key=lambda x: x.get('timestamp', ''))

    def _build_conversation_thread(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build a threaded conversation structure.

        Args:
            messages (List[Dict[str, Any]]): Raw messages from history

        Returns:
            List[Dict[str, Any]]: Threaded conversation structure
        """
        messages = self._sort_messages(messages)
        
        threaded = []
        message_map = {}

        for msg in messages:
            msg_copy = msg.copy()
            msg_copy['responses'] = []
            message_map[msg['message_id']] = msg_copy

            if msg['parent_id'] and msg['parent_id'] in message_map:
                message_map[msg['parent_id']]['responses'].append(msg_copy)
            else:
                threaded.append(msg_copy)

        return threaded

    def clear_history(self) -> None:
        """Clear the entire conversation history for the current workflow."""
        if self.history_file.exists():
            self.history_file.unlink()
            self.history_file.touch()

    def get_messages_by_entity(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Get all messages related to a specific entity.

        Args:
            entity_name (str): Name of the entity

        Returns:
            List[Dict[str, Any]]: All messages related to the entity
        """
        messages = []
        with open(self.history_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                if msg['sender_name'] == entity_name:
                    messages.append(msg)
        return self._sort_messages(messages)