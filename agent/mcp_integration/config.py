"""
MCP (Model Context Protocol) integration configuration.
Handles initialization of MultiServerMCPClient and tool discovery.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import (
    SSEConnection,
    StdioConnection,
    StreamableHttpConnection,
)


def get_servers_config_path() -> Path:
    """Get the path to the servers.yaml configuration file."""
    config_path = os.getenv("MCP_SERVERS_CONFIG_PATH")
    if config_path:
        return Path(config_path)

    # Default to servers.yaml in the same directory as this file
    return Path(__file__).parent / "servers.yaml"


def _expand_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Expand environment variables in configuration values."""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    else:
        return config


def _create_connection(server_name: str, server_config: dict[str, Any]) -> Any:
    """Create a connection object from server configuration."""
    transport = server_config.get("transport", "stdio")

    if transport == "stdio":
        connection = StdioConnection(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
        )
        # Add transport type for MCP client
        connection["transport"] = "stdio"
        return connection
    elif transport == "streamable_http":
        headers = server_config.get("headers", {})
        connection = StreamableHttpConnection(url=server_config["url"], headers=headers)
        connection["transport"] = "streamable_http"
        return connection
    elif transport == "sse":
        connection = SSEConnection(
            url=server_config["url"], headers=server_config.get("headers", {})
        )
        connection["transport"] = "sse"
        return connection
    else:
        raise ValueError(
            f"Unsupported transport type: {transport} for server: {server_name}"
        )


def get_mcp_client() -> MultiServerMCPClient:
    """Initialize and return MultiServerMCPClient with server configurations."""
    config_path = get_servers_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"MCP servers configuration not found at: {config_path}"
        )

    # Load and parse YAML configuration
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Expand environment variables
    config = _expand_env_vars(config)

    # Create connections dictionary
    connections = {}
    servers = config.get("servers", {})

    for server_name, server_config in servers.items():
        try:
            connection = _create_connection(server_name, server_config)
            connections[server_name] = connection
        except Exception as e:
            print(f"Warning: Failed to create connection for {server_name}: {e}")
            # Continue with other servers

    return MultiServerMCPClient(connections=connections)


async def initialize_mcp_tools() -> Any:
    """Initialize MCP client and return available tools."""
    client = get_mcp_client()

    # Connect to all configured servers
    # MCP client connects automatically

    # Get all available tools from connected servers
    tools = await client.get_tools()

    return tools


async def cleanup_mcp_client(client: MultiServerMCPClient | None = None) -> None:
    """Clean up MCP client connections."""
    if client is None:
        client = get_mcp_client()

    await client.close()
