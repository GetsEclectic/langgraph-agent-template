# LangGraph Agent Template - Claude Development Context

## CLAUDE.md Maintenance Guidelines

**Include in this file:**
- ✅ Current development status and immediate next priorities
- ✅ Working commands that are verified to work
- ✅ Critical constraints and non-negotiable standards  
- ✅ High-value patterns that are currently implemented
- ✅ Environment setup that actually works right now
- ✅ Repository structure and folder overview
- ✅ Immediate actionable information for agent handoff

**Do NOT include:**
- ❌ Speculative future patterns not yet implemented
- ❌ Comprehensive documentation (belongs in detailed docs)
- ❌ Code examples that create diagnostic noise
- ❌ Historical information that's not actionable
- ❌ Detailed explanations better suited for other files

**Goal:** Keep this file focused on what agents need to be immediately productive.

---

## Project Overview

**LangGraph Agent Template** is a complete starter template for building AI agents with LangGraph, featuring MCP integration, chat UI, and LangSmith observability.

**Core Features:**
- LangGraph ReAct agent with approval workflow
- MCP (Model Context Protocol) server integration
- Web-based chat UI for agent interaction
- LangSmith tracing and observability
- Comprehensive test suite

## Template Status

**✅ Template Features:**
- ✅ LangGraph ReAct agent foundation
- ✅ MCP filesystem server integration
- ✅ LangSmith tracing integration  
- ✅ Next.js chat UI
- ✅ Direct MCP tool execution for simplicity
- ✅ End-to-end test coverage

**🔧 Ready for customization** - clone and modify for your use case

## Development Environment

### Docker (Recommended)
```bash
# Development with hot reload
docker compose -f docker-compose.dev.yml up

# Production build
docker compose up

# Stop services
docker compose down

# Rebuild after changes
docker compose build

# Access at: http://localhost:40004
```

### Local Development (Alternative)
```bash
# Setup
source venv/bin/activate              # Always run first
pip install -e ".[dev]"              # Install dependencies

# Code quality (all working)
black . && ruff check . && mypy .    # Format, lint, type check
ruff check --fix .                   # Auto-fix linting issues

# Run services manually
python -m cli.agent serve --port 40003    # Start LangGraph server
cd agent-chat-ui && npm run dev -- --port 40004  # Start chat UI

# Test
pytest                                # Run test suite
```

## Repository Structure

**Core Directories:**
- `agent/` - Main agent implementation
  - Core agent logic (graph.py, prompts.py, state.py)
  - `mcp_integration/` - MCP server configuration and integration
- `cli/` - Command line interface (agent.py)
- `chat-ui/` - Next.js chat UI for web interaction
- `infra/` - Infrastructure and external integrations
  - `langsmith/` - LangSmith tracing configuration
- `tests/` - Test suite for template functionality
- `langgraph.json` - LangGraph server deployment configuration

## Key Architecture & Tech Stack

**Core Framework:** LangChain + LangGraph + LangSmith ecosystem  
**Model:** Claude 4 Sonnet via Anthropic API  
**External Tools:** MCP (Model Context Protocol) integration  
**Data:** Pydantic v2 models, UTC timestamps everywhere

## Critical Constraints

**Security:** MCP tools execute directly - add your own approval logic if needed  
**Observability:** LangSmith tracing on all operations  
**Quality:** Type hints mandatory, mypy strict mode  
**Testing:** End-to-end MCP integration tests
- NEVER skip tests when parts of them fail, want to know when something isn't working correctly, do not use pytest.skip or any other mechanism to skip tests when things don't work as expected

## Environment Variables

**Required:** Create `.env` in project root:
```bash
LANGSMITH_API_KEY=your_langsmith_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

**Chat UI:** Pre-configured in `agent-chat-ui/.env` (no setup needed)
- Uses `localhost:40003` for LangGraph server
- Uses `localhost:40004` for chat UI
- Contains no secrets, safe to commit

## Working LangSmith Integration

```python
# Import and use (already implemented)
from infra.langsmith.config import get_langsmith_client, LANGSMITH_PROJECT
from langsmith import traceable

@traceable
def your_function():
    # Automatically traced to LangSmith
    pass
```

**Status:** ✅ Live integration verified, traces flowing to dashboard

## Development Standards

**Type Safety:** All functions require type annotations, mypy in strict mode  
**Data Models:** Use Pydantic v2 for all data structures  
**Async Patterns:** Prefer async/await for I/O operations  
**UTC Time:** Use UTC timestamps everywhere, convert only at UI boundaries  
**Side Effects:** All writes require human approval gates