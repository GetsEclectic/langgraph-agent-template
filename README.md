# LangGraph Agent Template

A complete starter template for building AI agents with LangGraph, featuring MCP integration, chat UI, and LangSmith observability.

## ✨ Features

- **🤖 LangGraph ReAct Agent** - Ready-to-use agent with hardcoded prompts
- **🔌 MCP Integration** - Model Context Protocol server support (filesystem included)
- **💬 Agent Chat UI** - Next.js-based web interface for agent interaction
- **📊 LangSmith Tracing** - Built-in observability and monitoring
- **🚀 One-Command Setup** - Automated setup and start scripts
- **🧪 Test Suite** - End-to-end tests with MCP integration verification

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd <your-repo>

# One-time setup (installs everything)
./setup.sh
```

### 2. Configure Your Keys

Create `.env` in the project root:

```bash
# Required for agent functionality
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

### 3. Start the Agent

```bash
# Starts both LangGraph server and Chat UI
./start.sh

# Access the web chat at: http://localhost:40004
```

That's it! 🎉

**Alternative: Command Line Chat**
```bash
source venv/bin/activate
python -m cli.agent chat "Hello, what can you help me with?"
```

## 🛠️ Customization Guide

### Adding Your Own MCP Servers

1. **Edit MCP Configuration**
   ```yaml
   # agent/mcp_integration/servers.yaml
   servers:
     filesystem:
       command: "npx"
       args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
       transport: "stdio"
     
     # Add your server here
     your_server:
       command: "your-command"
       args: ["your", "args"]
       transport: "stdio"
   ```

2. **Add Environment Variables** (if needed)
   ```bash
   # .env
   YOUR_SERVER_TOKEN=your_token_here
   ```

### Customizing the Agent

1. **Agent Behavior** - Edit `agent/prompts.py`
2. **Agent State** - Modify `agent/state.py` 
3. **Agent Logic** - Update `agent/graph.py`

### Modifying the Chat UI

The chat UI is the official langchain agent-chat-ui in the `agent-chat-ui/` directory:

```bash
cd agent-chat-ui
npm run dev        # Development
npm run build      # Production build
npm run start      # Production server
```

**Configuration:** Pre-configured in `agent-chat-ui/.env` - no setup needed for localhost development.

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
├── agent-chat-ui/           # Next.js chat interface (pre-configured)
├── cli/                     # Command line interface
├── infra/                   # Infrastructure (LangSmith, etc.)
├── tests/                   # Test suite
├── setup.sh                 # One-time setup script
├── start.sh                 # Start both services script
└── langgraph.json          # LangGraph deployment config
```

## 🧪 Development

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_agent.py

# With output
pytest -v -s
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .
ruff check --fix .  # Auto-fix issues

# Type checking
mypy .
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

### Docker

```bash
# Build image
docker build -t my-agent .

# Run container
docker run -p 8000:8000 --env-file .env my-agent
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