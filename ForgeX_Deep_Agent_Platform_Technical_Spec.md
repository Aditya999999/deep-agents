# ForgeX Deep Agent Platform — Technical Requirements & Implementation Specification v2

**Status:** Updated implementation baseline  
**Date:** 27 August 2026  
**Audience:** Coding agent / engineering team  
**Scope:** Single-page skill-based Deep Agent application using FastAPI + React/Vite, SQLite, no authentication in v1

## 0. Executive decision summary

This version updates the supplied v1 specification to make the implementation decisions explicit.

### Locked decisions

- Repository layout is exactly:
  - `/backend` — Python/FastAPI/MVC application and Deep Agents integration
  - `/frontend` — React + Vite + TypeScript SPA
- LLM binding: **reuse the existing `azure_claude_chat.py` / `AzureClaudeChat` implementation**. Do not recreate the provider integration.
- Deep Agent runtime: use **LangChain `deepagents.create_deep_agent`** as the primary agent construction mechanism.
- Frontend runtime: use **`@langchain/react` v1 `useStream`** with **`HttpAgentServerAdapter`** against the custom FastAPI server.
- Persistence: **SQLite** for v1, including agent configuration data and LangGraph checkpoints. This is explicitly a single-instance/local development choice, not a production scale claim.
- Authentication: **not implemented in v1**. Keep an adapter boundary so authentication can be added later without rewriting the agent domain or UI components.
- UX: **single-page application**; agent configuration opens through drawers/modals/dialogs rather than separate routes.
- Runtime tool creation: supported only through a **safe allow-list of declarative tool types**. Arbitrary user Python/code execution is excluded from v1.
- Deep Agents beta/rapidly evolving features are not blindly exposed as UI knobs; they are either backend-managed or explicitly marked experimental.

### Architectural principle

The application must not re-implement functionality that Deep Agents / LangGraph / `@langchain/react` already owns. FastAPI should be a thin application boundary for configuration, persistence, security controls, protocol translation, and lifecycle management. React should consume framework-native stream state for messages, subagents, tool calls, todos, interrupts, and sandbox/artifact views.

## 1. Source and research basis

The supplied v1 document defines the original intent: a skill-based Deep Agent platform, FastAPI backend, React/Vite frontend, runtime system-prompt/skill/memory/tool configuration, SQLite as a candidate persistence option, and a custom adapter path for the Deep Agents frontend. It also identified custom `AgentServerAdapter` streaming as the principal technical risk.

This v2 has been reconciled against the current LangChain documentation and current GitHub issue/release activity checked on 27 August 2026.

### 1.1 Current framework capabilities verified

The current Deep Agents docs describe the harness as providing tools, virtual filesystem access, context management, skills, memory, summarization/context offloading, prompt caching, subagent delegation, optional task planning, and human approval/interrupts.

The current `create_deep_agent` surface includes:

`model`, `tools`, `system_prompt`, `middleware`, `subagents`, `skills`, `memory`, `permissions`, `backend`, `interrupt_on`, `response_format`, `state_schema`, `context_schema`, `checkpointer`, `store`, `debug`, `name`, and `cache`.

Therefore the old statement that the UI only needs to map a smaller set of parameters is no longer sufficient. This specification instead classifies each parameter as **UI-editable**, **preset/guarded**, or **backend-owned**.

### 1.2 Reliability findings that affect this design

The research baseline changed in several important ways:

- `deepagents` 0.7.x is active and changing rapidly. The latest release visible during this research was `deepagents==0.7.5` (August 2026). Version pinning is mandatory.
- The previously cited invalid-filesystem-path issue (#2463) is now **closed**, and its associated fix was merged upstream. This is still relevant as a regression test, but it should not be documented as an open defect.
- The previously cited tool-error issue (#947) is now **closed as not planned**. The problem pattern still matters, however, because newer issue activity documents tool exceptions escaping graph execution. All custom tools therefore remain required to return safe, user-readable errors instead of leaking raw exceptions.
- A newer tool-exception issue (#5354) remains active and references the historical mitigation of wrapping custom tools.
- A current open issue (#4820) reports that a dynamic skills-list documentation example can silently load zero skills when a leaf skill directory is supplied instead of its parent container. The implementation must validate skill roots and include a startup/test assertion that at least the intended skills are discoverable.
- Current SDK documentation says `HttpAgentServerAdapter` is the preferred starting point for a custom HTTP backend when the backend can expose the expected command and stream routes. This is the recommended integration here.

## 2. Product vision

ForgeX is a configurable, skill-based general-purpose Deep Agent. A user lands on a single conversation page, enters a task, optionally uploads files, and can configure the agent through dialogs without editing source code.

The agent should be able to:

- reason over multi-step tasks;
- use safe built-in universal tools;
- read/write within the configured virtual filesystem;
- load reusable skills progressively;
- load persistent `AGENTS.md` memory;
- delegate work to subagents;
- optionally maintain a todo/task plan;
- pause for human approval before sensitive operations;
- return structured output where configured;
- maintain checkpointed thread state;
- stream the run to the browser with visible messages, tool calls, subagent progress, todos, interrupts, and artifacts.

The UI should feel like the provided ForgeX references: dark, modern, translucent/glass panels, orange/red accents, rounded cards, strong left navigation, and a chat-first workspace. Configuration is secondary and appears as a modal/drawer over the main page.

## 3. Framework boundary — what we use vs what we own

| Concern | Framework-owned | ForgeX-owned |
|---|---|---|
| Agent orchestration | `deepagents` / LangGraph | Configuration lifecycle around agent instances |
| Planning | `TodoListMiddleware` | UI toggle/presentation |
| Subagents | Deep Agents task/subagent middleware | Configured subagent catalog and UI editor |
| Filesystem tools | Deep Agents | Safe root/path policy and per-agent permissions |
| Skills | Deep Agents skill loader | Skill CRUD/upload metadata and validation |
| Memory | Deep Agents `AGENTS.md` support | Memory editor and persistence path management |
| Model execution | Existing `AzureClaudeChat` | Model config validation and lifecycle |
| Streaming | LangGraph + Agent Streaming Protocol + `@langchain/react` | FastAPI endpoint and protocol adapter boundary |
| Tool calls | Deep Agents | Built-in custom tools and runtime declarative tool registry |
| Persistence | LangGraph checkpointing interfaces | SQLite wiring and agent-config repository |
| Authentication | Deferred | No auth logic in v1, clean seam reserved |
| UX state | `useStream` for agent run state | React UI layout/config modals |
| Observability | LangSmith integration | Config + environment toggles |

## 4. Target repository structure

```text
forge-x-deep-agent/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── dependencies.py
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── interfaces/
│   │   │   └── policies/
│   │   ├── application/
│   │   │   ├── agent_service.py
│   │   │   ├── agent_factory_service.py
│   │   │   ├── tool_service.py
│   │   │   ├── skill_service.py
│   │   │   ├── memory_service.py
│   │   │   ├── thread_service.py
│   │   │   ├── stream_service.py
│   │   │   └── interrupt_service.py
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   │   ├── sqlite.py
│   │   │   │   ├── models.py
│   │   │   │   └── repositories/
│   │   │   ├── deepagents/
│   │   │   │   ├── agent_builder.py
│   │   │   │   ├── backend_factory.py
│   │   │   │   ├── checkpoint_factory.py
│   │   │   │   └── skill_loader.py
│   │   │   └── streaming/
│   │   │       └── agent_server_protocol.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routers/
│   │   │       ├── health.py
│   │   │       ├── agent_configs.py
│   │   │       ├── tools.py
│   │   │       ├── skills.py
│   │   │       ├── memories.py
│   │   │       └── agent_stream.py
│   │   ├── tools/
│   │   │   ├── web_search.py
│   │   │   ├── http_fetch.py
│   │   │   ├── calculator.py
│   │   │   └── document_inspector.py
│   │   ├── middleware/
│   │   └── tests/
│   ├── azure_claude_chat.py       # EXISTING FILE: reused, not rewritten
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   ├── sidebar/
│   │   │   ├── agent-config/
│   │   │   ├── subagents/
│   │   │   ├── todos/
│   │   │   ├── tools/
│   │   │   └── artifacts/
│   │   ├── hooks/
│   │   │   ├── useAgentStream.ts
│   │   │   ├── useAgentConfig.ts
│   │   │   └── useThread.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   ├── lib/
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── README.md
│
├── README.md
└── .gitignore
```

## 5. Backend architecture — SOLID + MVC

FastAPI routes are the MVC/controller boundary. Pydantic DTOs and domain entities are the model boundary. Application services perform use-case orchestration. Infrastructure adapters encapsulate SQLite, Deep Agents, and streaming mechanics.

### 5.1 SOLID rules

**Single Responsibility:** routes do HTTP translation only; services do application orchestration; repositories do persistence; infrastructure adapters encapsulate external libraries.

**Open/Closed:** a new web-search provider, persistence adapter, or backend implementation should be added behind an interface rather than changing routers.

**Liskov Substitution:** repository/checkpointer/backend implementations must be interchangeable through narrow contracts.

**Interface Segregation:** keep agent configuration persistence, thread persistence, tool registry, skill repository, and stream transport contracts separate.

**Dependency Inversion:** application services depend on interfaces, and `api/deps.py` wires concrete implementations.

### 5.2 Important correction to the original MVC mapping

Do not force every framework object into a traditional MVC concept. `create_deep_agent`, LangGraph compiled graphs, checkpointers, and middleware are runtime/application infrastructure. MVC is used at the HTTP boundary, while the core remains domain/application/infrastructure layered.

## 6. Deep Agent construction model

### 6.1 Model binding

`AzureClaudeChat` remains the source of truth for the Azure-hosted Claude connection. The factory must receive or construct this existing `BaseChatModel` instance and pass it as `model=`.

Do not leak the API key, base URL, or model endpoint to the browser.

The factory should provide one centralized method:

```python
build_agent(config: AgentConfig) -> CompiledStateGraph
```

Internally it translates the persisted configuration into the current `create_deep_agent(...)` arguments.

### 6.2 `create_deep_agent` configuration matrix

| Parameter | V1 UI treatment | Reason |
|---|---|---|
| `model` | Read-only provider/model label | The server owns the existing AzureClaudeChat binding |
| `tools` | Editable selection | Safe and central to agent behavior |
| `system_prompt` | Editable | Explicit product requirement |
| `middleware` | Controlled presets only | Arbitrary middleware classes are code, not data |
| `subagents` | Editable through guarded form | Framework capability; validate names/descriptions/prompts |
| `skills` | Editable | Core skill-based requirement |
| `memory` | Editable | Core memory requirement |
| `permissions` | Editable through rule builder | Must be validated server-side |
| `backend` | Preset selection, advanced | Do not expose Python class construction |
| `interrupt_on` | Editable by tool | Core HITL capability |
| `response_format` | Presets + optional validated JSON Schema | Safe subset; no executable types |
| `state_schema` | Backend-owned | Python schema classes are not runtime data |
| `context_schema` | Backend-owned | Same reason; runtime context shape is an application contract |
| `checkpointer` | Backend-owned | SQLite implementation for v1 |
| `store` | Backend-owned | Infrastructure concern; required only by selected backend types |
| `debug` | Developer setting | Avoid end-user exposure in normal UI |
| `name` | Editable | Agent identity |
| `cache` | Backend-owned/policy setting | Provider/runtime infrastructure |

### 6.3 Backend defaults for v1

Recommended default construction:

- model: existing `AzureClaudeChat`
- system prompt: editable stored value with a safe default
- tools: calculator + web search + http fetch + document inspector
- skills: selected from `/data/agents/{agent_id}/skills/`
- memory: `/data/agents/{agent_id}/memory/AGENTS.md`
- backend: `StateBackend` for thread-local ephemeral filesystem state unless persistent filesystem behavior is explicitly enabled
- checkpointer: `AsyncSqliteSaver`
- planning: disabled by default, user-toggleable through a `TodoListMiddleware()` preset
- interrupt: enabled for `edit_file`, `delete`, `execute` where those capabilities are available; user-configurable for additional sensitive registered tools
- `execute`: disabled in v1 unless a real sandbox backend is added and tested
- subagents: default general-purpose subagent + user-defined synchronous subagents

## 7. Skills and memory design

### 7.1 Skills

Skills are directories containing `SKILL.md` plus optional resources. The runtime must pass the **parent container** of skill directories when using dynamic skill lists, then verify discovery.

Example storage:

```text
/data/agents/{agent_id}/skills/
├── requirements-analysis/
│   └── SKILL.md
├── tdd-generation/
│   ├── SKILL.md
│   └── templates/
└── code-review/
    └── SKILL.md
```

The UI supports:

- list installed skills;
- enable/disable skill per agent;
- upload a new skill directory or ZIP;
- edit `SKILL.md` text;
- validate frontmatter/name;
- preview skill metadata;
- test-load the skill before saving.

The backend must reject a skill if its root/path escapes the agent skill storage directory.

### 7.2 Memory

Memory is represented by `AGENTS.md` files. It is always loaded by the agent and therefore must not be treated like an on-demand skill.

The UI provides a markdown editor with:

- content validation;
- character/token advisory;
- save/version timestamp;
- restore previous version at a later stage.

SQLite stores metadata, while the actual markdown may be kept as a file under the agent's managed data root so it maps naturally to Deep Agents memory semantics.

## 8. Backend selection and persistence

### 8.1 SQLite decision

SQLite is accepted for v1 because the application is a single-page, local/single-instance application. It is useful for development and small deployments, but it should not be represented as a multi-instance production persistence architecture.

Use:

- **Agent configuration DB:** SQLAlchemy/SQLModel + SQLite + `aiosqlite`
- **LangGraph checkpointing:** `AsyncSqliteSaver` from `langgraph-checkpoint-sqlite`

The checkpointer must be wired into the compiled graph. The in-memory saver is for tests only.

### 8.2 What SQLite stores

Minimum tables/entities:

- `agent_configs`
- `agent_config_versions`
- `agent_tools`
- `tool_definitions`
- `agent_skills`
- `skills`
- `agent_memory_versions`
- `threads`
- optional `run_index` / run metadata for UI search

Checkpoint tables are owned by the LangGraph SQLite saver rather than duplicated in application tables.

### 8.3 Backend abstraction

Even though SQLite is locked for v1, repositories must use interfaces so Postgres can later replace SQLite without changing controllers or application services.

## 9. Built-in universal tools

Ship four built-in tools. All external calls must be exception-safe.

### 9.1 `web_search`

Purpose: search the public web and return concise structured results.

Provider is configurable by environment (`TAVILY`, `BING`, or an internal compatible provider). The application should select one concrete provider at startup, not expose provider credentials in the UI.

Return structure:

```json
{
  "query": "...",
  "results": [
    {"title": "...", "url": "...", "snippet": "..."}
  ]
}
```

### 9.2 `http_fetch`

Purpose: retrieve and normalize a public web page for reading.

Controls:

- HTTPS preferred;
- host allow-list for configurable enterprise deployments;
- block localhost/private/link-local address ranges to prevent SSRF;
- timeouts;
- response-size limits;
- content-type validation;
- redirect validation on every hop.

### 9.3 `calculator`

Purpose: deterministic arithmetic and simple structured calculations.

Never call Python `eval`. Use a restricted AST parser or a proven safe expression evaluator.

### 9.4 `document_inspector`

Purpose: inspect uploaded documents using existing parsing capabilities where practical. It should extract bounded text/metadata and expose it to the agent without creating a second conversation engine.

The tool is for document inspection; the agent itself remains the reasoning layer.

## 10. Runtime tool creation

Runtime tool creation is supported only for declarative templates.

### Supported v1 types

1. `http_request`
2. `webhook`
3. `composed_existing_tools`

### Explicitly excluded

- arbitrary Python
- arbitrary shell commands
- arbitrary code snippets
- user-provided executable plugins

### Feasibility flow

```text
UI tool form
   -> POST /api/tools/feasibility
   -> schema validation
   -> supported-type check
   -> security policy / SSRF / URL validation
   -> name collision check
   -> feasible=true/false + reasons
   -> save only when approved
```

The generated tool implementation must be a deterministic wrapper around a validated template. It must never compile or execute submitted source code.

## 11. Human-in-the-loop

Use Deep Agents `interrupt_on` for tools that may mutate state or incur meaningful external side effects.

Recommended v1 policy:

- `read_file`, `ls`, `glob`, `grep`: no approval
- `write_file`, `edit_file`: approval configurable, default enabled
- `delete`: approval mandatory
- `execute`: unavailable by default; if enabled later, approval mandatory
- user-created `http_request`/`webhook` tools: marked sensitive by default when side effects are possible

The frontend must render an approval dialog from the streamed interrupt state and submit the framework-compatible resume command. Do not create a second proprietary approval workflow.

## 12. Task planning

The current Deep Agents docs state that task planning is opt-in starting in v0.7. Use `TodoListMiddleware()` as a controlled preset.

The UI provides:

```text
Planning
[ ] Enable task planning
```

When enabled, the frontend renders `stream.values.todos` in a collapsible checklist. Todo states are `pending`, `in_progress`, and `completed`.

## 13. Subagents

The main coordinator may delegate via the framework's `task` tool.

The UI supports a guarded list of synchronous subagents:

```text
Name
Description
System prompt
Tools (optional)
Skills (optional)
Permissions (optional)
Interrupt policy (optional)
Response format (optional)
```

Do not make remote async subagents or arbitrarily configured compiled subgraphs a v1 requirement. They can be added later behind a separate infrastructure capability.

Also add a UI warning that custom subagents are isolated workers and return a report to the coordinator; users should not expect a subagent to behave like a separate chat participant.

## 14. Structured output

Support `response_format` as a **guarded** feature.

V1 UI options:

- Plain text (default)
- Markdown
- One of a few predefined application schemas (for example `summary`, `requirements`, `test_plan`)
- Advanced: JSON Schema editor with strict validation

Do not attempt to serialize arbitrary Python response schema classes through the browser.

## 15. State and context schemas

`state_schema` and `context_schema` are deliberately backend-owned in v1.

Reason: these are Python/type-level contracts used by graph execution, not simple end-user configuration fields. The product can expose business-level toggles that map to known state keys, but it should not allow users to inject arbitrary Python classes or code into the graph builder.

## 16. Streaming architecture

### 16.1 Required path

Use:

```text
React useStream
    |
    v1 @langchain/react
    |
HttpAgentServerAdapter
    |
HTTP/SSE
    |
FastAPI
    |
Agent Streaming Protocol adapter
    |
Compiled Deep Agent (LangGraph)
```

The current `@langchain/react` v1 documentation explicitly positions `HttpAgentServerAdapter` as the preferred path for a custom HTTP server when command and stream endpoints match its contract.

### 16.2 Adapter paths

Use the stock adapter with custom route mapping:

```ts
const transport = new HttpAgentServerAdapter({
  apiUrl: window.location.origin,
  paths: {
    commands: (threadId) => `/api/threads/${threadId}/commands`,
    stream: (threadId) => `/api/threads/${threadId}/stream`,
  },
});
```

Wrap creation in `useMemo` and let `useStream` manage the thread binding.

### 16.3 FastAPI stream contract

Minimum routes:

- `POST /api/threads/{thread_id}/commands`
- `GET /api/threads/{thread_id}/stream`
- `GET /api/threads/{thread_id}/state`
- `GET /api/threads/{thread_id}/history`

Configuration REST is separate:

- `GET/POST/PATCH /api/agent-configs...`
- `GET /api/tools`
- `POST /api/tools/feasibility`
- `POST /api/tools`
- `GET/POST/PATCH /api/skills...`
- `GET/PUT /api/agent-configs/{id}/memory`

### 16.4 SSE encoding

The browser adapter expects SSE frames in which the `data:` field contains the JSON Agent Protocol message. Preserve the protocol object intact.

Example framing:

```text
id: 42
event: message
data: {"type":"...","seq":42,...}

```

The backend must provide a bounded replay mechanism for a run so that a newly opened filtered stream can replay matching events without losing events emitted during connection timing windows. The current SDK reference documents this replay expectation explicitly.

### 16.5 Event translation

Implement `agent_server_protocol.py` as a dedicated module that:

1. consumes LangGraph/Deep Agents event streams;
2. maps them to Agent Protocol messages;
3. adds sequence/event IDs;
4. namespaces subagent information;
5. exposes tool-call progress and results;
6. preserves interrupt information;
7. exposes todo/custom state where available;
8. records a bounded replay buffer per thread/run.

Do not put event mapping code directly in FastAPI routers.

## 17. Frontend architecture

### 17.1 Stack

- React + TypeScript
- Vite
- `@langchain/react` v1
- `HttpAgentServerAdapter`
- React Query for configuration REST APIs only
- `useStream` as the single source of truth for live agent execution state

### 17.2 Landing-page layout

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Top bar: Home > Agent name          Help   Status   Agent settings      │
├───────────────┬───────────────────────────────────────────┬─────────────┤
│ Left sidebar  │ Main agent workspace                      │ Config      │
│               │                                           │ drawer /    │
│ Brand         │  Greeting / conversation                  │ modal       │
│ Nav icons     │                                           │             │
│ Fetch notes   │  User message                             │ Prompt      │
│ New convo     │  Assistant response                       │ Tools       │
│ Search        │  Tool card / subagent card / todo card    │ Skills      │
│ History       │                                           │ Memory       │
│               │ ────────────────────────────────────────  │ Subagents   │
│               │ Composer + upload + send/stop             │ Advanced    │
└───────────────┴───────────────────────────────────────────┴─────────────┘
```

The configuration panel should default to a right drawer on desktop and a full-height modal sheet on smaller screens.

### 17.3 Core components

- `AgentShell`
- `Sidebar`
- `ConversationList`
- `ChatTimeline`
- `AssistantMessage`
- `ToolCallCard`
- `SubagentCard`
- `TodoPanel`
- `InterruptApprovalDialog`
- `ArtifactPanel`
- `Composer`
- `AgentSettingsDrawer`
- `SystemPromptEditor`
- `ToolSelector`
- `ToolCreatorDialog`
- `SkillManagerDialog`
- `MemoryEditorDialog`
- `SubagentManagerDialog`
- `AdvancedSettingsAccordion`

### 17.4 Framework-native UI state

Use the Deep Agents frontend projections rather than duplicating state:

- `stream.messages`
- `stream.subagents`
- `stream.values`
- `useMessages(stream, subagent)`
- `useToolCalls(stream, subagent)`
- `useSubmissionQueue(stream)`
- interrupt state exposed by the stream

This is the key mechanism for keeping frontend code small and aligned with framework behavior.

## 18. Agent configuration UX

Open the configuration from a single gear/sliders action in the top bar.

### Basic tab

- Agent name
- System prompt
- Enabled tools
- Enabled skills
- Memory
- Planning on/off

### Behavior tab

- Response format
- Model parameter controls that the existing `AzureClaudeChat` actually supports
- Subagents
- Interrupt policy

### Advanced tab

- Filesystem backend mode
- Permission rules
- Debug mode
- Context/state diagnostics
- Experimental/beta features, clearly labeled

### Tools tab

- Built-in tools
- User-defined tools
- Create tool
- Feasibility check
- Sensitive-tool approval toggle

## 19. File upload strategy

User uploads should become agent-accessible files in the Deep Agents virtual filesystem rather than creating a second ad hoc RAG/chat path.

Flow:

```text
Browser upload
  -> FastAPI upload/command handling
  -> managed thread file root
  -> Deep Agents backend representation
  -> agent file tools / document_inspector
```

Constraints:

- file-size limits;
- allowed MIME types;
- generated safe file names;
- no raw OS path exposure;
- cleanup policy for abandoned thread files;
- test uploads for PDF/DOCX/plain text and selected image types supported by the configured model profile.

## 20. Security model for v1 without authentication

No user authentication is implemented, but **security boundaries are still required**.

Required:

- API keys remain server-side;
- CORS restricted to the Vite dev origin in development;
- request body/file-size limits;
- SSRF protection;
- path traversal prevention;
- strict runtime-tool allow-list;
- no arbitrary code execution;
- sensitive tool approval;
- rate limiting for expensive run creation where practical;
- structured error sanitization;
- secrets excluded from logs.

When authentication is added later, it should be inserted at the FastAPI dependency boundary and propagate an authenticated principal/user ID into the application service context. Agent business code should not depend directly on JWT/session implementations.

## 21. Environment configuration

```env
# Existing Azure-hosted Claude binding
AZURE_CLAUDE_API_KEY=REPLACE_ME
AZURE_CLAUDE_BASE_URL=REPLACE_ME
AZURE_CLAUDE_MODEL=REPLACE_ME

# SQLite application database
DATABASE_URL=sqlite+aiosqlite:///./forgex_agent.db
CHECKPOINT_DB_PATH=./forgex_checkpoints.db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Web search provider — select one
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=
BING_SEARCH_API_KEY=

# Runtime tool security
HTTP_TOOL_ALLOWED_HOST_SUFFIXES=
HTTP_TOOL_BLOCK_PRIVATE_NETWORKS=true

# LangSmith (optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=forgex-deepagent

# Dev controls
APP_ENV=development
DEBUG=false
```

The exact names of the three existing Claude variables must be reconciled to the current `azure_claude_chat.py` implementation before coding so the existing code is reused without an environment-name mismatch.

## 22. API contract

### Agent configuration

```text
POST   /api/agent-configs
GET    /api/agent-configs
GET    /api/agent-configs/{id}
PATCH  /api/agent-configs/{id}
DELETE /api/agent-configs/{id}
```

### Tools

```text
GET    /api/tools
POST   /api/tools/feasibility
POST   /api/tools
PATCH  /api/tools/{id}
DELETE /api/tools/{id}
```

### Skills and memory

```text
GET    /api/skills
POST   /api/skills
PATCH  /api/skills/{id}
DELETE /api/skills/{id}

GET    /api/agent-configs/{id}/memory
PUT    /api/agent-configs/{id}/memory
```

### Agent streaming

```text
POST   /api/threads/{thread_id}/commands
GET    /api/threads/{thread_id}/stream
GET    /api/threads/{thread_id}/state
GET    /api/threads/{thread_id}/history
```

The commands endpoint is the framework-facing control surface. Do not create separate application-only routes for each command type when the Agent Protocol can represent the command.

## 23. Error handling

Create one normalized error model for HTTP endpoints and one normalized event representation for runtime failures.

Rules:

1. Custom tools catch expected/unexpected exceptions.
2. Raw provider exceptions are logged server-side with correlation ID.
3. Browser receives a sanitized error message.
4. Tool failures should be rendered as tool failure cards rather than copied verbatim into the assistant transcript.
5. Stream failures close cleanly and leave the thread resumable whenever checkpoint state permits.

## 24. Caching / agent lifecycle

Agent construction is relatively expensive compared with reusing a compiled graph. Implement an `AgentInstanceCache` keyed by:

```text
(agent_config_id, agent_config_version, runtime_capability_signature)
```

Invalidate the cached compiled graph when a configuration version changes.

Never allow a stale compiled agent to silently execute after the user has published a new configuration.

The checkpointer/thread ID remains the source of conversation state; the compiled agent instance is a reusable execution definition.

## 25. Testing strategy

### 25.1 Unit tests

- `AgentFactoryService` mapping for every supported UI-editable `create_deep_agent` field
- configuration validation
- tool feasibility rules
- SSRF blocking
- path sanitization
- skill discovery/load validation
- memory file persistence
- permission rule evaluation
- response-format validation

### 25.2 Integration tests

- create config -> build agent -> run query
- run with calculator
- run with web search
- upload file -> inspect file
- subagent delegation -> stream subagent events
- planning enabled -> todos appear
- interrupt on sensitive tool -> approval -> resume
- SQLite restart -> config + checkpoint still available

### 25.3 Streaming contract tests

A dedicated protocol test must assert:

```text
open thread
 -> submit command
 -> stream begins
 -> message lifecycle emitted
 -> tool event emitted
 -> tool result emitted
 -> subagent discovery emitted when applicable
 -> todo custom state emitted when enabled
 -> final assistant message emitted
 -> run completion emitted
```

Also test:

- stream reconnect;
- replay from sequence/event ID;
- client filtering for subagents;
- interruption/resume;
- cancellation;
- malformed event protection.

## 26. Observability

Use LangSmith tracing as an optional environment-controlled capability. It is especially valuable here because Deep Agents is evolving quickly and the product exposes multiple layers: coordinator, tools, subagents, middleware, checkpointing, and custom transport.

Every server request should have a correlation ID, and the stream layer should include it in logs.

## 27. Dependency/version policy

### Backend

Pin the exact top-level versions used by the implementation, including at minimum:

- `deepagents==0.7.5` (baseline researched on 27 Aug 2026; re-check immediately before installation)
- compatible `langchain-core`
- compatible `langgraph`
- `langgraph-checkpoint-sqlite`
- FastAPI
- Uvicorn
- SQLAlchemy/SQLModel
- `aiosqlite`

Do not blindly paste versions for every transitive dependency from this document. Generate a lock/constraints snapshot from the actual tested environment and commit it.

### Frontend

Pin:

- React
- Vite
- TypeScript
- `@langchain/react` v1
- matching `@langchain/langgraph-sdk`
- React Query

The current reference page showed `@langchain/react` `HttpAgentServerAdapter` v1.0.29 during this research; verify the exact compatible pair at installation time and lock both.

## 28. FastAPI + Vite trade-off — final decision

### Why FastAPI stays

FastAPI gives the project ownership over MVC structure, configuration persistence, environment management, future authentication, enterprise policy enforcement, and the custom adapter/protocol edge while remaining natural for a Python Deep Agents runtime.

### What we give up

We must own the HTTP/SSE protocol boundary, run lifecycle, replay behavior, cancellation semantics, and persistence wiring that a hosted/managed LangGraph server could otherwise provide.

### Why Vite stays

Vite is a good fit for a single-page internal application. `@langchain/react` does not require Next.js for `useStream`; the main frontend adaptation is that some official examples are Next.js-oriented, so routing/server conventions should be ported rather than copied.

### The important trade-off

The architectural cost is therefore concentrated in the **FastAPI ↔ Agent Protocol ↔ `HttpAgentServerAdapter` boundary**. This is intentional. The alternative of writing a generic REST chat API plus custom React streaming state would reduce backend protocol work initially but would defeat the requirement to reuse Deep Agents UI capabilities and create more frontend code long-term.

## 29. Implementation phases

### Phase 0 — mandatory spike

1. Put the existing `azure_claude_chat.py` in `/backend`.
2. Install the pinned Deep Agents/LangGraph set.
3. Build one minimal `create_deep_agent` using `AzureClaudeChat`.
4. Add one built-in calculator tool.
5. Invoke a query and confirm tool calling.
6. Build one FastAPI command + SSE stream endpoint.
7. Connect a minimal Vite page using `HttpAgentServerAdapter` + `useStream`.
8. Confirm a tool call renders end-to-end.

**Do not build the settings UI before this spike passes.**

### Phase 1 — core backend

- MVC/SOLID skeleton
- SQLite config repository
- SQLite checkpointing
- agent factory
- built-in tools
- configuration CRUD
- thread lifecycle
- streaming protocol adapter

### Phase 2 — core frontend

- ForgeX landing page shell
- sidebar/history
- chat timeline
- composer/upload
- native tool/subagent/todo projections

### Phase 3 — configuration UX

- system prompt
- tools
- skills
- memory
- planning
- subagents
- response format
- permission/interrupt dialogs

### Phase 4 — advanced runtime

- declarative runtime tools
- feasibility checks
- structured schema configuration
- artifact view
- stream reconnect/replay UX

### Phase 5 — hardening

- protocol contract tests
- security tests
- restart/persistence tests
- observability
- dependency lock
- packaging/run scripts

## 30. Definition of done

The v1 implementation is complete when a user can:

1. open the single landing page;
2. create/select an agent configuration;
3. edit system prompt;
4. enable/disable built-in tools;
5. create a safe declarative runtime tool after feasibility approval;
6. enable skills and edit memory;
7. toggle planning;
8. configure guarded subagents;
9. configure sensitive-tool approval;
10. upload a document;
11. enter a natural-language task;
12. watch coordinator messages stream;
13. watch tool calls and results stream;
14. watch subagent progress when delegation occurs;
15. see todos when planning is enabled;
16. approve/reject an interrupt when configured;
17. continue a previous SQLite-backed thread;
18. refresh the browser without losing checkpointed state;
19. avoid exposing any provider/API secret to the browser;
20. run without adding authentication code in v1.

## 31. Known limitations / explicit non-goals

- no login/SSO;
- no multi-tenant authorization;
- no arbitrary runtime Python;
- no unsandboxed `execute` tool;
- no production multi-instance SQLite architecture;
- no dynamic arbitrary `state_schema`/`context_schema` authored from the UI;
- no dependence on deprecated CLI/server patterns;
- no proprietary replacement for the Agent Streaming Protocol when `HttpAgentServerAdapter` can be used.

## 32. Research references

1. LangChain — Deep Agents overview: https://docs.langchain.com/oss/python/deepagents/overview
2. LangChain — Deep Agents customization / `create_deep_agent`: https://docs.langchain.com/oss/python/deepagents/customization
3. LangChain — Deep Agents frontend overview: https://docs.langchain.com/oss/python/deepagents/frontend/overview
4. LangChain — Deep Agents backends: https://docs.langchain.com/oss/python/deepagents/backends
5. LangChain — Deep Agents skills: https://docs.langchain.com/oss/python/deepagents/skills
6. LangChain — Deep Agents memory: https://docs.langchain.com/oss/python/deepagents/memory
7. LangChain — Deep Agents human-in-the-loop: https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
8. LangChain — LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
9. LangChain JS/React v1 migration: https://github.com/langchain-ai/langgraphjs/blob/main/libs/sdk-react/docs/v1-migration.md
10. LangChain JS/React custom transport: https://github.com/langchain-ai/langgraphjs/blob/main/libs/sdk-react/docs/custom-transport.md
11. Deep Agents GitHub releases: https://github.com/langchain-ai/deepagents/releases
12. Deep Agents issue #5354 (tool exceptions): https://github.com/langchain-ai/deepagents/issues/5354
13. Deep Agents issue #2463 (filesystem invalid path, now closed/fixed upstream): https://github.com/langchain-ai/deepagents/issues/2463
14. Deep Agents issue #947 (tool-call error handling, closed as not planned): https://github.com/langchain-ai/deepagents/issues/947
15. Deep Agents issue #4820 (dynamic skill-list documentation/behavior report): https://github.com/langchain-ai/deepagents/issues/4820

---

## Appendix A — v1 to v2 changes

| Original v1 assumption | v2 update |
|---|---|
| Listed only a subset of `create_deep_agent` settings | Reconciled against current full signature |
| Treated #2463 as open | Now documented as closed/fixed upstream |
| Treated #947 as open | Now documented as closed as not planned |
| Relied on old endpoint shape centered on `/runs` | Uses current adapter-oriented `/commands` + `/stream` contract |
| Open question: SQLite vs Postgres | **Resolved: SQLite for v1** |
| Open question: auth | **Resolved: no auth for v1** |
| Open question: custom adapter vs AG-UI | **Resolved: `HttpAgentServerAdapter` / Agent Protocol path** |
| Runtime tool creation could appear like arbitrary generation | Explicitly constrained to declarative allow-listed types |
| `execute` could be implicitly assumed | Disabled in v1 unless sandbox capability is added |
| Skills were described as directly loading a selected leaf path | Parent-container validation required |
| All framework parameters could be end-user knobs | Classified into editable / guarded / backend-owned |

## Appendix B — first coding-agent prompt

Implement the project exactly under `/backend` and `/frontend` using this v2 specification. Before building the configuration UI, complete Phase 0 and prove the `AzureClaudeChat -> create_deep_agent -> FastAPI Agent Protocol -> HttpAgentServerAdapter -> useStream` path with one tool call. Keep framework-owned behavior in Deep Agents/LangGraph and keep FastAPI limited to application policy, persistence, configuration, and protocol boundary code. Do not add authentication, arbitrary runtime code execution, or a second chat-state engine in v1.
