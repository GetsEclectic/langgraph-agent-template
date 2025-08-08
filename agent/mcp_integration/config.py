"""
MCP (Model Context Protocol) integration configuration.
Minimal wrapper around langchain_mcp_adapters per upstream docs:
https://github.com/langchain-ai/langchain-mcp-adapters

We simply:
- Load YAML at agent/mcp_integration/servers.yaml (or MCP_SERVERS_CONFIG_PATH)
- Expand ${ENV_VAR} occurrences
- Pass the resulting servers mapping directly to MultiServerMCPClient
"""

import os
from pathlib import Path
from typing import Any

import yaml
from langchain_mcp_adapters.client import MultiServerMCPClient


def get_servers_config_path() -> Path:
    """Return path to servers.yaml (overridable via MCP_SERVERS_CONFIG_PATH)."""
    config_path = os.getenv("MCP_SERVERS_CONFIG_PATH")
    if config_path:
        return Path(config_path)
    return Path(__file__).parent / "servers.yaml"


def _expand_env_vars(value: Any) -> Any:
    """Recursively expand ${VAR} patterns using process environment."""
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.getenv(env_var, value)
    return value


def get_mcp_client() -> MultiServerMCPClient:
    """
    Create a MultiServerMCPClient from the YAML configuration.
    The YAML shape should match the dict expected by MultiServerMCPClient, e.g.:

    servers:
      math:
        command: "python"
        args: ["./examples/math_server.py"]
        transport: "stdio"
      weather:
        url: "http://localhost:8000/mcp/"
        transport: "streamable_http"
        headers:
          Authorization: ${WEATHER_TOKEN}
    """
    path = get_servers_config_path()
    if not path.exists():
        raise FileNotFoundError(f"MCP servers configuration not found at: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    raw = _expand_env_vars(raw)
    servers = raw.get("servers", {}) or {}

    # Pass the servers mapping directly as in upstream docs.
    return MultiServerMCPClient(servers)
