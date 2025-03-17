"""
Debugger module for logging and debugging AI interactions.

This module provides a Debugger class that handles logging for agents and supervisors,
organizing logs within the nexus_workflows directory structure when part of a workflow,
or in a standalone logs directory when used independently.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List


class Debugger:
    """
    A debug logging utility for AI agents and supervisors.

    This class manages debug logging, organizing logs either within a workflow's
    directory structure or in a standalone logs directory. It supports various
    logging levels and formats for different types of data.

    Attributes:
        name (str): Name of the entity (agent/supervisor) being logged
        logger (logging.Logger): The logger instance for this entity
        log_file_path (Path): Path to the log file
    """

    STANDALONE_LOG_DIR = Path('nexus_workflows') / 'standalone_logs'

    def __init__(self, 
                 name: str, 
                 workflow_id: Optional[str] = None,
                 log_level: int = logging.DEBUG):
        """
        Initialize the Debugger instance.

        Args:
            name (str): Name of the entity (agent/supervisor) being logged
            workflow_id (Optional[str]): ID of the workflow if part of one
            log_level (int): Logging level (default: logging.DEBUG)
        """
        self.name = name
        self.workflow_id = workflow_id
        self.log_level = log_level
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up or reconfigure the logger with current settings."""
        # Determine log directory
        if self.workflow_id:
            log_dir = Path('nexus_workflows') / self.workflow_id / 'logs'
        else:
            log_dir = self.STANDALONE_LOG_DIR
            
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up log file path
        self.log_file_path = log_dir / f"{self.name}.log"
        
        # Create a unique logger name
        logger_name = self.name
        
        # Remove existing logger if it exists
        if logger_name in logging.root.manager.loggerDict:
            logging.root.manager.loggerDict.pop(logger_name)
        
        # Create new logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self.log_level)
        
        # Remove any existing handlers
        self.logger.handlers.clear()
        
        # Create and configure file handler
        file_handler = logging.FileHandler(self.log_file_path, mode='a')
        file_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False

    def update_workflow_id(self, workflow_id: str) -> None:
        """
        Update the workflow ID and move logs to the workflow directory.

        This method is called when an agent or assistant supervisor is
        registered with a workflow.

        Args:
            workflow_id (str): The new workflow ID
        """
        old_log_path = self.log_file_path
        self.workflow_id = workflow_id
        
        # Reconfigure logger with new workflow_id
        self._setup_logger()
        
        # Move existing logs if they exist
        if old_log_path.exists() and old_log_path != self.log_file_path:
            try:
                with open(old_log_path, 'r') as source:
                    with open(self.log_file_path, 'a') as dest:
                        dest.write('\n' + source.read())
                # Remove the old log file
                old_log_path.unlink()
            except Exception as e:
                self.log(f"Error moving logs: {str(e)}", level="error")

        # Log the transition
        self.log(f"Logging continued in workflow: {workflow_id}")

    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message at the specified level.

        Args:
            message (str): The message to log
            level (str): The logging level (debug/info/warning/error/critical)
        """
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)

        # Ensure message is written immediately
        for handler in self.logger.handlers:
            handler.flush()

    def log_dict(self, data: Dict, message: str = "") -> None:
        """
        Log a dictionary with optional message.

        Args:
            data (Dict): The dictionary to log
            message (str): Optional message to precede the dictionary
        """
        self.log(f"{message}\n{json.dumps(data, indent=2)}")

    def log_list(self, data: List, message: str = "") -> None:
        """
        Log a list with optional message.

        Args:
            data (List): The list to log
            message (str): Optional message to precede the list
        """
        self.log(f"{message}\n{json.dumps(data, indent=2)}")

    def start_session(self) -> None:
        """Log the start of a new session."""
        self.log(f"------ New Session Started for {self.name} ------")

    def end_session(self) -> None:
        """Log the end of the current session."""
        self.log(f"------ Session Ended for {self.name} ------")

    def __str__(self) -> str:
        """Return string representation of the Debugger instance."""
        return f"Debugger(name={self.name}, log_file={self.log_file_path})"

    def __repr__(self) -> str:
        """Return detailed string representation of the Debugger instance."""
        return (f"Debugger(name={self.name}, "
                f"log_file={self.log_file_path}, "
                f"level={self.log_level})")