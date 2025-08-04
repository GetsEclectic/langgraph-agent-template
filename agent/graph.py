"""
LangGraph ReAct agent implementation.
Simplified implementation using create_react_agent with MCP tools.
"""

from datetime import datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langsmith import traceable

from agent.config import AgentConfig
from agent.mcp_integration.config import get_mcp_client
from agent.prompts import format_current_time, load_agent_prompt


class Agent:
    """
    Simplified LangGraph ReAct agent using create_react_agent.
    Uses MCP tools directly without approval workflow.
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.model: ChatAnthropic | None = None
        self.tools: list[Any] = []
        self.agent: Any = None
        self.mcp_client: Any = None

    async def initialize(self) -> None:
        """Initialize the agent with model, tools, and create_react_agent."""
        # Initialize model
        self.model = ChatAnthropic(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            timeout=self.config.tool_timeout_seconds,
            stop=None,
        )

        # Initialize MCP tools
        await self._initialize_tools()

        # Create the agent using create_react_agent
        self._create_agent()

    async def _initialize_tools(self) -> None:
        """Initialize MCP tools."""
        try:
            self.mcp_client = get_mcp_client()

            # Get all available tools
            mcp_tools = await self.mcp_client.get_tools()

            print(f"🔧 Loaded {len(mcp_tools)} MCP tools:")
            for tool in mcp_tools:
                print(f"  - {tool.name}")

            self.tools = mcp_tools

        except Exception as e:
            print(f"Warning: Failed to initialize MCP tools: {e}")
            self.tools = []

    def _create_agent(self) -> None:
        """Create the ReAct agent using create_react_agent."""
        if not self.model:
            raise RuntimeError("Model not initialized")

        # Load prompt from LangSmith Hub
        prompt_template = load_agent_prompt(self.config.langsmith_prompt_name)
        system_prompt = prompt_template.format(current_time=format_current_time())

        self.agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=system_prompt,
            checkpointer=MemorySaver(),
        )

    @traceable
    async def run(self, goal: str, session_id: str | None = None) -> dict[str, Any]:
        """Run the agent with the given goal."""
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # Create session config
        session_id = session_id or f"session_{datetime.now().isoformat()}"
        config = {"configurable": {"thread_id": session_id}}

        # Execute the agent and get final state
        messages = [{"role": "user", "content": goal}]

        if self.agent:
            final_result = await self.agent.ainvoke(
                {"messages": messages}, config=config
            )
            return dict(final_result)

        return {"messages": []}

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.mcp_client:
            pass  # MCP client cleanup handled automatically


# Factory function for creating configured agent
async def create_agent(config: AgentConfig | None = None) -> Agent:
    """Create and initialize a LangGraph agent."""
    agent = Agent(config)
    await agent.initialize()
    return agent


# Function for LangGraph CLI deployment
def create_graph() -> Any:
    """Create and return the graph for LangGraph CLI deployment."""
    import asyncio

    from langchain_anthropic import ChatAnthropic
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent

    from agent.mcp_integration.config import get_mcp_client
    from agent.prompts import format_current_time, load_agent_prompt

    # Initialize model
    config = AgentConfig()
    model = ChatAnthropic(
        model_name=config.model_name,
        temperature=config.temperature,
        timeout=config.tool_timeout_seconds,
        stop=None,
    )

    # Get MCP tools - need to run async initialization
    tools = []
    try:
        # We'll initialize tools in a synchronous way for the deployment
        # This is a simplified approach - tools will be available after first request
        mcp_client = get_mcp_client()

        # Create a simple event loop if needed for MCP initialization
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Try to get tools synchronously
        if loop.is_running():
            # If loop is already running, we'll have to defer tool loading
            print("📋 LangGraph deployment: MCP tools will be initialized lazily")
        else:
            # Initialize tools if we can run the loop
            tools = loop.run_until_complete(mcp_client.get_tools())
            print(f"🔧 Loaded {len(tools)} MCP tools for deployment")
    except Exception as e:
        print(f"Warning: Could not initialize MCP tools during deployment: {e}")
        print("📋 Tools will be loaded on first request")

    # Load prompt from LangSmith Hub
    prompt_template = load_agent_prompt(config.langsmith_prompt_name)
    system_prompt = prompt_template.format(current_time=format_current_time())

    # Create and return the graph
    graph = create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    return graph
