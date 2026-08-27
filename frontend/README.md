# ForgeX Deep Agent Platform — Frontend

React + Vite + TypeScript Single Page Application (SPA) designed with dark theme, glassmorphism, orange/red accents, conversation timeline, tool call cards, todo task plans, and self-learning memory inspection drawers.

## Features

- **Chat Workspace**: Streamed assistant responses, user bubbles, markdown rendering, tool call execution status cards, collapsible todo checklists.
- **Self-Learning & Feedback**: 👍 / 👎 feedback actions on assistant messages that directly teach the agent and update its knowledge base.
- **Agent Configuration Drawer**:
  - **Basic**: Agent name, system prompt, task planning toggle
  - **Tools**: Toggle built-in `@tool` tools (Calculator, Web Search, HTTP Fetch, Document Inspector)
  - **Memory & Learning**: Inspect episodic interactions, learned semantic knowledge, edit `AGENTS.md`, view live learning event audit logs
  - **Behavior**: Response format schemas, subagent management, interrupt policy
  - **Advanced**: Backend mode, server model binding, debug mode
- **Sidebar**: Conversation search, thread switching, rename/delete context actions, and memory stats summary.

## Running Locally

```bash
# Install dependencies
npm install

# Start Vite development server (proxies /api to http://localhost:8000)
npm run dev

# Build production bundle
npm run build
```
