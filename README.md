# ForgeX Deep Agent Platform

A skill-based, self-learning Deep Agent platform built with **FastAPI**, **React + Vite + TypeScript**, **SQLite**, and **Azure-hosted Anthropic Claude**.

---

## 🌟 Overview & Architecture

ForgeX is a single-page Deep Agent workspace that enables multi-step task reasoning, safe built-in universal tools, virtual filesystem workflows, human-in-the-loop approvals, and a continuous **self-learning & multi-layer memory system**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Top bar: ForgeX > Agent name           Learnings Count   Agent settings │
├───────────────┬───────────────────────────────────────────┬─────────────┤
│ Left sidebar  │ Main agent workspace                      │ Config      │
│               │                                           │ drawer      │
│ Brand         │  Greeting / conversation                  │             │
│ Nav icons     │                                           │ Basic       │
│ New convo     │  User message                             │ Tools       │
│ Search        │  Assistant response (streaming)           │ Memory 🧠   │
│ History       │  Tool card / task plan checklist          │ Behavior    │
│ Memory Stats  │  Thumbs up/down feedback                  │ Advanced    │
│               │ ────────────────────────────────────────  │             │
│               │ Composer + upload + send/stop             │             │
└───────────────┴───────────────────────────────────────────┴─────────────┘
```

### Key Capabilities

1. **Self-Learning & Multi-Layer Memory**:
   - **Working Memory**: Dynamic thread context injected per run.
   - **Episodic Memory**: Automatically records key interactions and outcomes from past conversations.
   - **Semantic Memory**: Automatically infers user preferences, corrections, and domain knowledge with confidence scores.
   - **AGENTS.md**: Persistent user-editable markdown memory.
   - **Feedback Loop**: 👍 / 👎 actions trigger post-run knowledge reinforcement and learning log updates.
2. **LangChain `@tool` Universal Built-in Tools**:
   - `calculator`: Safe AST-based expression evaluator (no `eval`).
   - `web_search`: Structured web search with Tavily/Bing integration and fallback simulation.
   - `http_fetch`: URL fetcher with SSRF prevention, content-type checks, and bounded response sizes.
   - `document_inspector`: Text extraction and metadata analysis for files.
3. **Agent Streaming Protocol (SSE)**:
   - Real-time streaming of messages, tool execution, todos, and run lifecycle events with bounded replay buffers.
4. **Azure Claude LLM Binding**:
   - Production-ready `AzureClaudeChat` integrating directly with Azure-hosted Anthropic Claude endpoints, featuring connection pooling, retries, and automatic local fallback when credentials are not yet configured.

---

## 📂 Repository Layout

```text
forge-x-deep-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI entry point, CORS, lifespan
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic Settings (.env configuration)
│   │   │   └── logging.py                 # JSON logging with correlation IDs
│   │   ├── application/
│   │   │   ├── agent_service.py           # Command processing & SSE streaming
│   │   │   ├── agent_factory_service.py   # Agent compilation & instance cache
│   │   │   ├── tool_service.py            # Tool registry & feasibility checks
│   │   │   ├── skill_service.py           # Skill management
│   │   │   ├── memory_service.py          # Multi-layer memory manager
│   │   │   └── learning_service.py        # Self-learning & feedback engine
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   │   ├── sqlite.py              # Async SQLAlchemy engine
│   │   │   │   ├── models.py              # ORM entities (Configs, Tools, Memory, Threads)
│   │   │   │   └── repositories/          # Eager-loaded async CRUD repositories
│   │   │   ├── deepagents/
│   │   │   │   ├── agent_builder.py       # Deep Agent compiler
│   │   │   │   ├── backend_factory.py     # State/persistent filesystem factory
│   │   │   │   ├── checkpoint_factory.py  # Checkpoint path resolver
│   │   │   │   └── skill_loader.py        # Skill discovery & path traversal guard
│   │   │   └── streaming/
│   │   │       └── agent_server_protocol.py # SSE formatting & replay buffer
│   │   ├── api/
│   │   │   ├── deps.py                    # Dependency injection
│   │   │   └── routers/                   # REST & SSE routers (health, configs, tools, skills, memories, stream)
│   │   └── tools/                         # Built-in tools with @tool decorator
│   │       ├── calculator.py
│   │       ├── web_search.py
│   │       ├── http_fetch.py
│   │       └── document_inspector.py
│   ├── azure_claude_chat.py               # AzureClaudeChat model binding
│   ├── requirements.txt                   # Pinned Python dependencies
│   ├── .env.example                       # Environment template
│   └── tests/                             # Unit & integration test suites
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                        # Complete ForgeX single-page UI
│   │   ├── index.css                      # Design system (dark theme, glass, accents)
│   │   ├── main.tsx                       # React root
│   │   ├── types/index.ts                 # TypeScript interfaces
│   │   ├── services/api.ts                # REST client & EventSource SSE stream consumer
│   │   └── hooks/                         # Custom React hooks (useAgentStream, useAgentConfig, useThread)
│   ├── package.json
│   ├── vite.config.ts                     # Vite proxy config
│   └── tsconfig.json
│
├── ForgeX_Deep_Agent_Platform_Technical_Spec.md # v2 Technical Specification
└── README.md                              # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env

# 3. (Optional) Provide your real Azure Claude and/or Tavily credentials in .env:
# AZURE_CLAUDE_API_KEY=your-azure-claude-key
# AZURE_CLAUDE_BASE_URL=https://your-resource.services.ai.azure.com/models
# AZURE_CLAUDE_MODEL=claude-sonnet-4-5-forgex-rnd

# 4. Start the FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at `http://localhost:8000` (interactive Swagger documentation at `http://localhost:8000/docs`).

### 2. Frontend Setup

In a new terminal:

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the Vite development server
npm run dev
```

The frontend SPA will be accessible at `http://localhost:5173`. Requests to `/api/*` are automatically proxied to `http://localhost:8000`.

---

## 🧪 Testing & Validation

### Run Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

All 9 automated unit and integration tests verify:
- Safe AST Calculator (arithmetic, functions, zero-division, code execution prevention)
- HTTP Fetch SSRF protection (loopback/private IP rejection, schema validation)
- Agent Factory caching & version invalidation
- Health endpoint & configuration/tools API flows

### Run Frontend Build Validation

```bash
cd frontend
npm run build
```

---

## 🔒 Security Baseline

- **API Keys**: Stored exclusively server-side in `.env`; never exposed to browser clients.
- **SSRF Prevention**: Loopback (`127.0.0.1`, `localhost`), link-local, and RFC 1918 private subnets are blocked on URL fetching tools.
- **No `eval()`**: Calculator parses expression trees via Python `ast` within a strict whitelist of operators and mathematical functions.
- **Path Traversal Protection**: Skill loaders and file inspectors reject paths attempting to escape the configured root directories.
- **HITL Safeguards**: Configurable approval policies for sensitive operations.