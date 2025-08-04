"""
Configuration models for the LangGraph agent.
"""

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for the LangGraph agent."""

    # Model configuration
    model_name: str = "claude-sonnet-4-20250514"
    temperature: float = 0.1
    max_tokens: int = 4000

    # Tool configuration
    max_tool_calls_per_turn: int = 5
    tool_timeout_seconds: int = 30

    # Time settings (all UTC)
    default_timezone: str = "UTC"

    # Tracing and observability
    enable_langsmith_tracing: bool = True
    langsmith_project: str = "langgraph-agent-template"

    # Prompt management (required)
    langsmith_prompt_name: str = "langgraph-agent-system-prompt"
