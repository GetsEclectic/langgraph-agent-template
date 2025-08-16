# LangGraph Agent Template - Claude Development Context

## CLAUDE.md Maintenance Guidelines

Include in this file:
- ✅ Current development status and immediate next priorities
- ✅ Working commands that are verified to work
- ✅ Critical constraints and non-negotiable standards  
- ✅ High-value patterns that are currently implemented
- ✅ Environment setup that actually works right now
- ✅ Repository structure and folder overview
- ✅ Immediate actionable information for agent handoff

Do NOT include:
- ❌ Speculative future patterns not yet implemented
- ❌ Comprehensive documentation (belongs in detailed docs)
- ❌ Code examples that create diagnostic noise
- ❌ Historical information that's not actionable
- ❌ Detailed explanations better suited for other files

Goal: Keep this file focused on what agents need to be immediately productive.

---

## Project Overview

LangGraph Agent Template is a complete starter template for building AI agents with LangGraph, featuring MCP integration, chat UI, and LangSmith observability.

Core Features:
- LangGraph ReAct agent with approval-ready workflow hooks
- MCP (Model Context Protocol) server integration (configured via JSON)
- Web-based chat UI for agent interaction
- LangSmith tracing and observability

Status: Ready for customization — clone and modify for your use case

Note: CLI and test suite have been removed to simplify runtime. The deployment path is via LangGraph server (make_graph) and the web UI.

---

## Development Environment

### Containers (Only)
```bash
# Start both agent and chat UI
docker compose up -d

# Stop services
docker compose down

# Rebuild after changes
docker compose build

# Access the chat UI at: http://localhost:40004
```


---

## Repository Structure

Core Directories:
- `agent/` - Main agent implementation
  - `graph.py` - graph factory (`make_graph`) used by LangGraph server
  - `prompts.py` - System prompts
  - `config.py` - Agent configuration
  - `mcp_integration/` - MCP server configuration and integration
- `agent-chat-ui/` - Next.js chat UI for web interaction
- `infra/` - Infrastructure and external integrations
  - `langsmith/` - LangSmith tracing configuration
- `langgraph.json` - LangGraph server deployment configuration

Removed:
- `cli/` (command line interface) — removed
- `tests/` (test suite) — removed

---

## Key Architecture & Tech Stack

Core Framework: LangChain + LangGraph + LangSmith  
Model: Claude 4 Sonnet via Anthropic API  
External Tools: MCP (Model Context Protocol) integration  
Data: Pydantic v2 models, UTC timestamps everywhere

---

## Critical Constraints

Security: MCP tools execute directly — add your own approval logic if needed  
Observability: LangSmith tracing on all operations  
Quality: Type hints mandatory, mypy strict mode  
Async Patterns: Prefer async/await for I/O operations  
UTC Time: Use UTC timestamps everywhere, convert only at UI boundaries  
Side Effects: All writes require human approval gates

---

## Environment Variables

Required: Create `.env` in project root:
```bash
LANGSMITH_API_KEY=your_langsmith_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Chat UI: Pre-configured in `agent-chat-ui/.env` (no secrets)
- Uses `localhost:40003` for LangGraph server
- Uses `localhost:40004` for chat UI

---

## Working LangSmith Integration & Evaluations

```python
# Import and use (already implemented)
from infra.langsmith.config import get_langsmith_client, LANGSMITH_PROJECT
from langsmith import traceable

@traceable
def your_function():
    # Automatically traced to LangSmith
    pass
```

Run YAML-driven evaluations inside the container:

```bash
docker compose exec agent python scripts/run_evaluation.py \
  --dataset-file infra/langsmith/examples/sample_dataset.yaml \
  --json
```

YAML schema:
```yaml
dataset:
  name: my-eval-dataset
  description: Optional description
  judge_model: anthropic:claude-3-5-sonnet-latest
  examples:
    - inputs:
        question: "What is 2 + 2?"
      outputs:
        answer: "4"
```

Status: Live integration verified, traces flow to dashboard

---

## Runtime & MCP Tools

- The server exports `make_graph()` (in `agent/graph.py`).
- MCP tools are loaded via `agent/mcp_integration/config.py` with fallback logic:
  - `servers.json` at project root (if exists) - custom config, gitignored
  - `agent/mcp_integration/servers.json` - default template config
- Follow LangGraph MCP docs: call `get_tools()` and pass into `create_react_agent`.

Healthcheck endpoints:
- Dev Compose: `/docs` (basic liveness)
- Prod Compose: `/threads` POST healthcheck is used elsewhere; either endpoint indicates server is up.

---
