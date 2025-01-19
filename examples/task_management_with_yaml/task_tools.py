tasks = ["Implement YAML config", "Write tests", "Update documentation"]

def add_task(task: str) -> str:
    """
    Add a new task to the task list.

    Args:
        task (str): The task to be added.

    Returns:
        str: Confirmation message.
    """
    tasks.append(task)
    return f"Task added: {task}"

def list_tasks() -> str:
    """
    List all current tasks.

    Returns:
        str: Numbered list of all tasks.
    """
    return "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))

def calculate_priority(urgency: int, importance: int) -> int:
    """
    Calculate the priority of a task.

    Args:
        urgency (int): The urgency of the task (1-10).
        importance (int): The importance of the task (1-10).

    Returns:
        int: The calculated priority.
    """
    return urgency * importance