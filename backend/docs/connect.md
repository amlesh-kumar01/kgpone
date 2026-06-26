# Connecting KnowledgeOS MCP Server to AI Assistants

The KnowledgeOS backend includes a **Model Context Protocol (MCP)** server built with `FastMCP`. MCP allows standard AI assistants (like ChatGPT, Claude, and Gemini) to seamlessly discover and execute local tools exposed by the platform.

When connected, these assistants can:
1. Search course catalogs and departments natively.
2. Query the KnowledgeOS GraphRAG pipeline for answers.
3. Automatically retrieve syllabus topics and prerequisites.
4. Execute specialized study guide prompts.

## Prerequisites

1. Ensure the KnowledgeOS backend is running locally.
2. Verify the MCP server script works by running `uv run src/mcp.py` in the `backend` directory.

---

## 1. Connecting to Claude Desktop (Recommended)

Claude Desktop natively supports the Model Context Protocol.

1. Open Claude Desktop.
2. Navigate to **Settings** > **Developer**.
3. Open your Claude configuration file (usually located at `~/Library/Application Support/Claude/claude_desktop_config.json` on Mac, or `%APPDATA%\Claude\claude_desktop_config.json` on Windows).
4. Add the KnowledgeOS MCP server configuration:

```json
{
  "mcpServers": {
    "knowledgeos": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "E:/HACKATHONS/innovation_challenge/KgpOne/backend",
        "src/mcp.py"
      ]
    }
  }
}
```
*(Make sure to adjust the `args` directory path to point to your absolute path of the `backend` folder).*

5. Restart Claude Desktop.
6. Claude will now have a **"Tools"** icon in the chat interface. You can ask Claude to "Search for CS101 documents" or "Tell me about the prerequisites for CS101", and it will trigger the tools directly!

---

## 2. Connecting to ChatGPT (Via Custom GPT Actions)

ChatGPT does not yet have a native local MCP client for the desktop app, but you can expose the MCP tools via OpenAI Custom Actions (if you have ChatGPT Plus).

### Option A: Local Tunneling (Development)
1. Since ChatGPT is hosted in the cloud, it needs a way to reach your local API. Use a tunnel like `ngrok`:
   ```bash
   ngrok http 8000
   ```
2. Go to **ChatGPT > Explore > Create a GPT**.
3. Under the **Configure** tab, click **Create new action**.
4. You will need an OpenAPI schema for the tools. Since KnowledgeOS is built on FastAPI, the schema is automatically generated! Simply paste your ngrok URL with the openapi path:
   `https://<your-ngrok-id>.ngrok-free.app/openapi.json`
5. ChatGPT will automatically parse the `/api/v1/query/ask` and `/api/v1/query/search` routes as available tools. You can now chat with the Custom GPT, and it will execute API calls directly against your local GraphRAG backend!

### Option B: Using an MCP-to-OpenAI Gateway
There are open-source bridges that map local MCP servers to the OpenAI chat interface:
1. Use an open source client like `mcp-cli` or third-party wrappers that translate MCP tool calls into OpenAI function calls.
2. Configure the gateway to connect to your local `src/mcp.py` process.

---

## 3. Connecting to Gemini Pro

Similar to ChatGPT, Gemini interacts with external APIs via **Extensions** or **Function Calling** (if using the API).

1. **Using Gemini API (Function Calling)**:
   The backend's `PlannerService` currently uses Gemini's Function Calling under the hood to route intents. If you are building a custom UI for Gemini, you can export the MCP definitions into Gemini's `tools` array.

2. **Using Google AI Studio / Gemini Web**:
   Currently, the Gemini web UI does not natively support pointing to a local MCP config file (like Claude Desktop does). 
   To expose KnowledgeOS to the Gemini Web UI:
   - Wait for Google to release native MCP support for the Gemini app.
   - Or, wrap the API in a Google Workspace Add-on or OAuth app, allowing Gemini to invoke the KnowledgeOS endpoints via standard REST calls (using `ngrok` for local testing).

---

## Testing Your Connection

Regardless of the AI assistant, once connected, you should be able to type prompts like:

*   *"List all the departments in KnowledgeOS."* -> Triggers `list_departments()`
*   *"What are the topics covered in CS101?"* -> Triggers `get_course_topics()`
*   *"Help me understand graph traversals based on my course documents."* -> Triggers `answer_course_question()`

The AI will parse your natural language, invoke the KnowledgeOS Hybrid RAG, and return the deeply contextualized answer!
