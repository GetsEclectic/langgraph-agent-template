"""
LangGraph ReAct agent implementation.
Exports an async make_graph() per langchain-mcp-adapters docs.
"""

from typing import Any

from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from agent.summarization import make_recent_tool_response_summarizer

from agent.config import AgentConfig
from agent.mcp_integration.config import get_mcp_client
from agent.prompts import format_current_time, load_agent_prompt, safe_format_prompt


async def make_graph() -> Any:
    """
    Build and return the graph for LangGraph API server.

    Follows upstream guidance:
    - Initialize the model
    - Create MultiServerMCPClient
    - await client.get_tools()
    - Pass tools directly to create_react_agent
    """
    # Initialize model config
    config = AgentConfig()
    model = ChatAnthropic(
        model_name=config.model_name,
        temperature=config.temperature,
        timeout=config.tool_timeout_seconds,
        stop=None,
    )

    # Summarize only the most recent ToolMessage if it is very large
    summarizer_hook = make_recent_tool_response_summarizer(
        model,
        trigger_tokens=8000,
        summary_max_tokens=256,
    )

    # Load prompt
    prompt_template = load_agent_prompt(config.langsmith_prompt_name)
    system_prompt = safe_format_prompt(prompt_template, current_time=format_current_time())

    # Initialize MCP tools
    client = get_mcp_client()
    tools = await client.get_tools()

    # Create and return the graph
    graph = create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt,
        pre_model_hook=summarizer_hook,
        checkpointer=MemorySaver(),
    )
    # Increase default recursion limit from 25 to 50
    graph = graph.with_config(recursion_limit=50)
    return graph
