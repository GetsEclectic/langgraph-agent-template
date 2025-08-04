# LangGraph Agent Template

A complete starter template for building AI agents with LangGraph, featuring MCP integration, chat UI, and LangSmith observability.

## ✨ Features

- **🤖 LangGraph ReAct Agent** - Ready-to-use agent
- **🔌 MCP Integration** - Model Context Protocol server support (filesystem included)
- **💬 Langchain Chat UI** - Next.js-based web interface for agent interaction
- **📊 LangSmith Tracing** - Built-in observability and monitoring
- **🎯 LangSmith Prompt Hub** - Centralized prompt management and A/B testing
- **🧪 Test Suite** - End-to-end tests with MCP integration verification

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and setup
git clone <your-repo>
cd <your-repo>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure Your Keys

Edit `.env` with your API keys:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Optional: Customize project name
LANGSMITH_PROJECT=your-project-name
```

### 3. Set Up Your Prompt in LangSmith Hub

The template uses LangSmith Prompt Hub for prompt management. This allows you to iterate on prompts without code changes:

1. **Go to LangSmith Prompts**: https://smith.langchain.com/prompts
2. **Create a new prompt** with the name: `langgraph-agent-system-prompt`
3. **Copy the default template** from `agent/prompts.py` (see the docstring)
4. **Save and publish** your prompt
5. **Optional**: Update `langsmith_prompt_name` in `agent/config.py` if using a different name

**Benefits of LangSmith Prompt Hub:**
- 🔄 Iterate on prompts without code changes
- 📊 A/B test different prompt versions
- 👥 Collaborate on prompt development
- 📈 Track performance metrics per prompt version

### 4. Test Your Setup

```bash
# Run tests to verify everything works
pytest

# Check code quality
black . && ruff check . && mypy .
```

### 5. Start the Agent

Choose your preferred interface:

**Option A: Command Line Chat**
```bash
python -m cli.agent chat "Hello, what can you help me with?"
```

**Option B: Web Chat UI**
```bash
# Terminal 1: Start LangGraph server
python -m cli.agent serve

# Terminal 2: Start chat UI
cd chat-ui
npm install
npm run dev

# Open http://localhost:3000
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

The chat UI is the langchain-chat-ui Next.js application in the `chat-ui/` directory:

```bash
cd chat-ui
npm run dev        # Development
npm run build      # Production build
npm run start      # Production server
```

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
│   ├── prompts.py           # System prompts and templates
│   ├── config.py            # Agent configuration options
│   └── mcp_integration/     # MCP server configuration
├── chat-ui/                 # Next.js chat interface
├── cli/                     # Command line interface
├── infra/                   # Infrastructure (LangSmith, etc.)
├── tests/                   # Test suite
├── .env.example             # Environment template
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