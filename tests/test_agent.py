"""
Test suite for LangGraph Agent Template.
Verifies that the agent can be initialized and MCP integration works end-to-end.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from agent.graph import AgentConfig, create_agent  # noqa: E402


@pytest.mark.asyncio
async def test_agent_initialization() -> None:
    """Test that the agent can be initialized properly."""

    agent = await create_agent(AgentConfig())

    # Check that components are properly set up
    assert agent.model is not None, "Model not initialized"
    assert agent.agent is not None, "Agent not created"
    assert len(agent.tools) > 0, "No tools available"

    await agent.cleanup()


@pytest.mark.asyncio
async def test_mcp_filesystem_integration() -> None:
    """Test MCP filesystem integration end-to-end with actual tool call."""

    agent = await create_agent(AgentConfig())

    # Test simple directory listing or file reading
    goal = "List the files in the current directory using MCP filesystem tools"
    result = await agent.run(goal, session_id="test-mcp-filesystem")

    messages = result.get("messages", [])
    assert len(messages) > 0, "No messages returned from agent"

    # Get the final response message
    final_message = messages[-1].content if messages else ""

    # Check for successful filesystem operation indicators
    success_indicators = [
        "file",
        "directory",
        "folder",
        ".py",
        ".md",
        ".yaml",
        ".json",
        "listed",
        "found",
        "contents",
    ]

    has_filesystem_content = any(
        indicator in final_message.lower() for indicator in success_indicators
    )

    print(f"\n📁 Final agent response: {final_message[:300]}...")
    print(f"✅ Has filesystem content: {has_filesystem_content}")

    assert (
        has_filesystem_content
    ), f"Agent response doesn't indicate successful filesystem operation. Response: {final_message}"


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Load environment variables for all tests."""
    # Change to project root to find .env file
    os.chdir(project_root)
    load_dotenv()

    # Check required environment variables
    required_vars = ["ANTHROPIC_API_KEY", "LANGSMITH_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        pytest.skip(f"Missing environment variables: {missing_vars}")
