"""
MCP (Model Context Protocol) integration configuration.
Minimal wrapper around langchain_mcp_adapters per upstream docs:
https://github.com/langchain-ai/langchain-mcp-adapters

We simply:
- Load JSON at agent/mcp_integration/servers.json (default) or servers.json at project root (override)
- Expand ${ENV_VAR} occurrences
- Pass the resulting servers mapping directly to MultiServerMCPClient
"""

import os
import json
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient


def get_servers_config_path() -> Path:
    """
    Return path to servers.json with fallback logic:
    1. servers.json at project root (if exists)
    2. agent/mcp_integration/servers.json (default)
    
    This function is robust to missing files and different environments.
    """
    # Try multiple possible project root locations
    possible_roots = [
        Path(__file__).parent.parent.parent,  # Local development
        Path("/app/project_root"),  # Docker container mounted project root
        Path("/app"),  # Docker container app directory
        Path.cwd(),   # Current working directory
    ]
    
    for project_root in possible_roots:
        root_servers_json = project_root / "servers.json"
        if root_servers_json.exists() and root_servers_json.is_file():
            return root_servers_json
    
    # Use default location as fallback
    default_path = Path(__file__).parent / "servers.json"
    return default_path


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
    Create a MultiServerMCPClient from the JSON configuration.
    The JSON shape should match the dict expected by MultiServerMCPClient, e.g.:

    {
      "servers": {
        "math": {
          "command": "python",
          "args": ["./examples/math_server.py"],
          "transport": "stdio"
        },
        "weather": {
          "url": "http://localhost:8000/mcp/",
          "transport": "streamable_http",
          "headers": {
            "Authorization": "${WEATHER_TOKEN}"
          }
        }
      }
    }
    """
    path = get_servers_config_path()
    if not path.exists():
        raise FileNotFoundError(f"MCP servers configuration not found at: {path}")

    with open(path, "r") as f:
        raw = json.load(f) or {}

    raw = _expand_env_vars(raw)
    servers = raw.get("servers", {}) or {}

    # Pass the servers mapping directly as in upstream docs.
    return MultiServerMCPClient(servers)
