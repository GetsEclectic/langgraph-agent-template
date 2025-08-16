# LangGraph Agent Template

A complete starter template for building AI agents with LangGraph, featuring MCP integration, chat UI, and LangSmith observability.

## ✨ Features

- **🤖 LangGraph ReAct Agent** - Ready-to-use agent with hardcoded prompts
- **🔌 MCP Integration** - Model Context Protocol server support (filesystem included)
- **💬 Agent Chat UI** - Next.js-based web interface for agent interaction
- **📊 LangSmith Tracing** - Built-in observability and monitoring
- **🐳 Docker Ready** - Containerized development with hot reload
- **⚡ Fast Setup** - One command to start everything

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone <your-repo>
cd <your-repo>

# Create environment file
cp .env.example .env
# Edit .env and add your API keys:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# LANGSMITH_API_KEY=your_langsmith_api_key_here
```

### 2. Start with Docker (Recommended)

```bash
# Start both agent and chat UI
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Access the chat UI at: http://localhost:40004** 🎉


## 🛠️ Customization Guide

### Adding Your Own MCP Servers

1. **MCP Configuration Options**
   
   The system uses `agent/mcp_integration/servers.json` by default. To customize without affecting the template:
   
   ```bash
   # Create your own servers.json at project root (gitignored)
   cp agent/mcp_integration/servers.json servers.json
   # Edit servers.json with your configuration
   ```
   
   **Configuration priority:**
   - `servers.json` at project root (if exists) - your custom config
   - `agent/mcp_integration/servers.json` - default template config

2. **Edit MCP Configuration**
   ```json
   {
     "servers": {
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
         "transport": "stdio"
       },
       "your_server": {
         "command": "your-command",
         "args": ["your", "args"],
         "transport": "stdio"
       }
     }
   }
   ```

3. **Add Environment Variables** (if needed)
   ```bash
   # .env
   YOUR_SERVER_TOKEN=your_token_here
   ```

### Customizing the Agent

1. **Agent Behavior** - Edit `agent/prompts.py`
2. **Agent State** - Modify `agent/state.py` 
3. **Agent Logic** - Update `agent/graph.py`

### Modifying the Chat UI

The chat UI lives in `agent-chat-ui/`. For development and builds, use the provided containers.

### Adding Approval Workflow (Optional)

The template uses direct tool execution for simplicity. If you need approval gates for write operations:

1. **Create an approval wrapper class** in `agent/graph.py`
2. **Wrap tools during initialization** based on operation type  
3. **Use LangGraph interrupts** to pause execution for approval
4. **Add approval handling** in your UI or CLI

Example approval wrapper:
```python
from langgraph.types import interrupt

class ApprovalTool(BaseTool):
    def _run(self, **kwargs):
        if self._is_write_operation():
            approval = interrupt({"type": "approval", "tool": self.name})
            if not approval.get("approved"):
                return "Operation cancelled"
        return self.wrapped_tool.run(**kwargs)
```

## 📁 Project Structure

```
/
├── agent/                   # Core agent implementation
│   ├── graph.py             # LangGraph agent definition  
│   ├── prompts.py           # System prompts (hardcoded)
│   ├── config.py            # Agent configuration options
│   └── mcp_integration/     # MCP server configuration
├── agent-chat-ui/           # Next.js chat interface
│   ├── Dockerfile           # Chat UI container
│   └── .env                 # Pre-configured for localhost
├── infra/                   # Infrastructure (LangSmith, etc.)
├── Dockerfile               # Agent container
├── docker-compose.yml       # Development with hot reload (default)
├── docker-compose.prod.yml  # Production Docker setup
└── langgraph.json          # LangGraph deployment config
```

## 🧪 Development

### Code Quality

```bash
docker compose exec agent black . && \
docker compose exec agent ruff check . && \
docker compose exec agent mypy .
```

### Evaluations

1. Create a YAML dataset (see sample at `infra/langsmith/examples/sample_dataset.yaml`).
2. Run the evaluation inside the agent container:

```bash
docker compose exec agent python scripts/run_evaluation.py \
  --dataset-file infra/langsmith/examples/sample_dataset.yaml \
  --json
```

YAML schema:

```yaml
dataset:
  name: my-eval-dataset            # required
  description: Optional description
  judge_model: anthropic:claude-3-5-sonnet-latest
  examples:
    - inputs:
        question: "What is 2 + 2?"
      outputs:
        answer: "4"
```

## 📊 Observability

This template includes LangSmith integration for:

- **Tracing** - Every agent run is automatically traced
- **Datasets** - Manage test cases and evaluations  
- **Monitoring** - Track performance and costs

View your traces at: https://smith.langchain.com

## 🚀 Deployment

### LangGraph Cloud

```bash
# Deploy to LangGraph Cloud
langgraph deploy

# Or use the included configuration
langgraph deploy --config langgraph.json
```

### Docker Production

```bash
# Production build and run
docker compose -f docker-compose.prod.yml up -d

# Scale services
docker compose -f docker-compose.prod.yml up -d --scale agent=3

```

### Manual Docker Build

```bash
# Build agent image
docker build -t my-agent .

# Build chat UI image  
docker build -t my-chat-ui ./agent-chat-ui

# Run with custom configuration
docker run -p 40003:40003 --env-file .env my-agent
docker run -p 40004:40004 my-chat-ui
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- 📖 **Documentation**: Check the `CLAUDE.md` file for development context
- 🐛 **Issues**: Report bugs via GitHub issues
- 💬 **Discussions**: Use GitHub discussions for questions

---
