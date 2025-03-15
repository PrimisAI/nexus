# Dictionary to store tasks per context
context_tasks = {}

def add_task_with_context(task: str, context: str) -> str:
    """
    Add a new task with context information.
    Args:
        task (str): The task to be added
        context (str): The context/category for the task
    Returns:
        str: Confirmation message
    """
    if context not in context_tasks:
        context_tasks[context] = []
    context_tasks[context].append(task)
    return f"Task added to {context}: {task}"

def list_context_tasks(context: str) -> str:
    """
    List all tasks in a specific context.
    Args:
        context (str): The context/category to list tasks from
    Returns:
        str: List of tasks in the context
    """
    if context not in context_tasks:
        return f"No tasks found in context: {context}"
    tasks = context_tasks[context]
    return "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))

def get_contexts() -> str:
    """
    Get all available contexts.
    Returns:
        str: List of all contexts
    """
    if not context_tasks:
        return "No contexts available"
    return "\n".join(f"- {context} ({len(tasks)} tasks)" for context, tasks in context_tasks.items())