import json, subprocess, time
from typing import Dict, Any

class ToolsBucket:
    def execute_command(self, argument: str) -> Dict[str, Any]:
        """
                Execute a command in the persistent terminal session.

                Args:
                    argument (str): A JSON string containing the command to execute.

                Returns:
                    Dict[str, Any]: A dictionary indicating the status ('success' or 'error') and output.
                """
        try:
            # Parse the input argument to extract the command
            values = json.loads(argument)
            command = values['argument'] + '\n'  # Append newline to simulate pressing Enter

            subprocess.run(["tmux", "send-keys", "-t", "my_session", command, "C-m"])
            time.sleep(2)
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", "my_session", "-p", "-S", "-1000", "-J"],  # capture last 1000 lines of terminal
                stdout=subprocess.PIPE,
                text=True)
            output = result.stdout.strip()
            return {"status": "success", "output": output}
        except Exception as e:
            return {"status": "error", "output": str(e)}
