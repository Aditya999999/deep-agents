# ForgeX Deep Agent Platform — Backend

FastAPI-powered Deep Agent backend with SQLite persistence, Agent Streaming Protocol (SSE), LangChain `@tool` decorator tools, Azure Claude integration (`AzureClaudeChat`), and self-learning multi-layer memory.

## Architecture

- **Web Framework**: FastAPI with CORS, correlation ID middleware, and async lifespan hooks
- **Database**: SQLite with async SQLAlchemy + `aiosqlite`
- **LLM Binding**: `azure_claude_chat.py` (`AzureClaudeChat`) supporting Azure-hosted Anthropic Claude endpoints with retries, timeouts, and fallback reasoning
- **Tools**:
  - `calculator` (`@tool`): Safe AST-based math evaluator
  - `web_search` (`@tool`): Async web search with Tavily/Bing provider support
  - `http_fetch` (`@tool`): Async URL fetcher with SSRF protection, size bounds, and content validation
  - `document_inspector` (`@tool`): Text extraction and metadata inspection for uploaded files
- **Memory & Self-Learning**:
  - `AGENTS.md` structured persistent memory
  - Episodic memory for key conversation interactions
  - Semantic memory for learned preferences and domain facts
  - Learning engine with post-conversation insight extraction and feedback loop
- **Streaming**:
  - Agent Server Protocol SSE streaming with replay buffers and command endpoints (`/commands`, `/stream`, `/state`, `/history`)

## Configuration (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set your real credentials:

```env
# Azure Claude
AZURE_CLAUDE_API_KEY=your-azure-claude-api-key
AZURE_CLAUDE_BASE_URL=https://your-resource.services.ai.azure.com/models
AZURE_CLAUDE_MODEL=claude-sonnet-4-5-forgex-rnd

# Database
DATABASE_URL=sqlite+aiosqlite:///./forgex_agent.db
CHECKPOINT_DB_PATH=./forgex_checkpoints.db

# Optional Web Search
TAVILY_API_KEY=your-tavily-key
```

## Running the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run server on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Running Tests

```bash
python -m pytest tests/ -v
```
