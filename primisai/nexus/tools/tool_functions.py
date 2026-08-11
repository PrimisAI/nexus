
import json
import logging
import re
import subprocess
import shlex
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Shell metacharacters that MUST NOT appear inside a single command token
_SHELL_METACHAR_RE = re.compile(r"[;&|`$(){}<>\\!\n\r\t#~]")
# Maximum number of chars allowed in a single command invocation.
_MAX_COMMAND_LENGTH = 4096
_DEFAULT_TMUX_SESSION = "nexus_tool_session"


def _validate_command_token(command: str) -> None:
    """Raise ValueError if command text contains unsafe shell patterns."""
    if not isinstance(command, str) or not command.strip():
        raise ValueError("command argument must be a non-empty string")
    if len(command) > _MAX_COMMAND_LENGTH:
        raise ValueError(
            f"command argument is too long: {len(command)} > {_MAX_COMMAND_LENGTH}"
        )
    # shlex.quote refuses to quote NUL bytes; reject those up front.
    if "\x00" in command:
        raise ValueError("command argument contains NUL byte(s)")
    m = _SHELL_METACHAR_RE.search(command)
    if m:
        bad = repr(m.group(0))
        raise ValueError(
            f"command argument contains forbidden shell character {bad}. "
            "Command chaining / redirection / subshell expansion is disabled "
            "inside ToolsBucket.execute_command for safety."
        )


class ToolsBucket:
    def execute_command(self, argument: str) -> dict[str, Any]:
        """
                Execute a command in a persistent terminal session.

                Args:
                    argument (str): A JSON string containing the command to execute.
                        Expected shape (new optional fields):
                            ``{"argument": "<shell cmd>", "session_name": "<tmux session>", "capture_lines": 1000}``

                Returns:
                    Dict[str, Any]: A dictionary indicating the status ('success' or 'error') and output.
                """
        try:
            # Parse the input argument to extract the command
            values = json.loads(argument)
            if not isinstance(values, dict) or "argument" not in values:
                raise ValueError("JSON argument must contain an 'argument' key")

            raw_command = values["argument"]
            session_name = values.get("session_name", _DEFAULT_TMUX_SESSION)
            capture_lines = int(values.get("capture_lines", 1000))

            # Validate the session name (tmux allows most chars but keep it sane)
            if not isinstance(session_name, str) or not session_name.strip():
                raise ValueError("session_name must be a non-empty string")
            if re.search(r"[\s:]", session_name):
                raise ValueError(
                    "session_name may not contain whitespace or colons (tmux session naming rules)"
                )

            # Validate the command text against unsafe characters
            _validate_command_token(raw_command)

            # Append exactly one newline to simulate pressing Enter after the command
            command_token = raw_command + "\n"

            # ALWAYS use argv-form subprocess (NO shell=True) 
            subprocess.run(
                ["tmux", "send-keys", "-t", session_name, command_token, "C-m"],
                check=False,
            )
            time.sleep(2)

            result = subprocess.run(
                [
                    "tmux",
                    "capture-pane",
                    "-t",
                    session_name,
                    "-p",
                    "-S",
                    f"-{capture_lines}",
                    "-J",
                ],
                stdout=subprocess.PIPE,
                text=True,
                check=False,
            )
            output = result.stdout.strip()
            return {"status": "success", "output": output}
        except Exception as e:
            logger.warning(f"execute_command failed: {e}")
            return {"status": "error", "output": str(e)}
