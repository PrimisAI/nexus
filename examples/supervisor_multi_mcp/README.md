# Supervisor Multi-MCP Example

This example shows how to use a `Supervisor` to manage agents powered by different MCP tool servers:
- A weather info agent (using MCP stdio transport)
- An addition/math agent (using MCP SSE transport)

## Folder Contents

- `add_server.py` &mdash; MCP SSE server providing an `add(a, b)` tool on port 8000.
- `weather_server.py` &mdash; MCP stdio server providing weather tools (`get_alerts`, `get_forecast`).
- `example_multi_mcp.py` &mdash; Main supervisor/agent orchestrator and chat frontend.
- `README.md` &mdash; This info.


## Setup and Usage

1. **Start the Addition SSE Server**

   In one terminal:
   ```
   python add_server.py
   ```

2. **(Nothing to run for Weather Stdio! The agent code will launch weather_server.py as needed.)**

3. **Start the Supervisor Chat**

   In another terminal:
   ```
   python example_multi_mcp.py
   ```

   - Ask: `What are the weather alerts for NY?`
   - Ask: `What is 2 plus 4?`
   - Mix weather and math prompts; the supervisor will route queries!

## Pro Tips

- The agent graph will be displayed before chat.
- No need to run `weather_server.py` manually; agent launches it via stdio as a subprocess.
- You can extend with more agents and tool servers, using either MCP transport.
