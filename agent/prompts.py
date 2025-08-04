"""
LangSmith Prompt Hub integration for the LangGraph agent.
Loads prompts from LangSmith for better prompt management and experimentation.

To set up your prompt in LangSmith Hub:
1. Go to https://smith.langchain.com/prompts
2. Create a new prompt with name: "langgraph-agent-system-prompt"
3. Use this template as your starting point:

---
You are a helpful AI agent built with LangGraph and MCP integration.

## Your Capabilities
You have access to various tools through the Model Context Protocol (MCP) and should use them to help users accomplish their goals. Your available tools depend on which MCP servers are configured.

## General Approach
- Be helpful and accomplish any request that can be completed using your available tools
- Always ask for clarification when requests are ambiguous
- Use the most appropriate tools for each task
- Provide clear, concise responses about what you've accomplished

## Available Tools
This template includes a filesystem MCP server that provides:
- **File Operations**: Read, write, create, and delete files
- **Directory Operations**: List directory contents, create directories
- **File Management**: Move, copy, and manage file permissions

Additional MCP servers can be configured in `agent/mcp_integration/servers.yaml`

## Guidelines
1. **Use UTC timestamps when working with time-sensitive data**
2. **Be precise and methodical in your reasoning**
3. **Ask for clarification if goals are ambiguous**
4. **Respect user privacy and data security**
5. **Use appropriate tools for each task**

## Time Context
Current UTC time: {current_time}

## Response Format
Use clear reasoning with these steps:
1. **Understand**: Clarify the goal and requirements
2. **Plan**: Break down the approach and identify needed tools
3. **Execute**: Use the appropriate tools to accomplish the task
4. **Complete**: Summarize results and next steps

Always be helpful, precise, and transparent about what you're doing and why.
---

4. Save and publish the prompt
5. Update agent/config.py with your prompt name if different
"""

from datetime import UTC, datetime

from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def load_agent_prompt(prompt_name: str) -> str:
    """Load system prompt from LangSmith Prompt Hub."""
    try:
        prompt = hub.pull(prompt_name)
        # If it's a ChatPromptTemplate, extract the system message
        if hasattr(prompt, "messages") and prompt.messages:
            for message in prompt.messages:
                if hasattr(message, "prompt") and hasattr(message.prompt, "template"):
                    return str(message.prompt.template)
            raise ValueError("No system message found in ChatPromptTemplate")
        # If it's a simple prompt template
        elif hasattr(prompt, "template"):
            return str(prompt.template)
        # If it's just a string
        elif isinstance(prompt, str):
            return prompt
        else:
            raise ValueError(f"Unexpected prompt format from hub: {type(prompt)}")
    except Exception as e:
        raise RuntimeError(
            f"Failed to load prompt '{prompt_name}' from LangSmith Hub: {e}"
        ) from e


def create_agent_prompt(prompt_name: str) -> ChatPromptTemplate:
    """Create the main agent prompt template from LangSmith Hub."""
    system_prompt = load_agent_prompt(prompt_name)

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ]
    )


def format_current_time() -> str:
    """Format current UTC time for prompts."""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
