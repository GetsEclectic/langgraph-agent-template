import os

from langsmith import Client


def get_langsmith_client() -> Client:
    """Initialize LangSmith client with environment variables."""
    return Client(
        api_url=os.getenv("LANGSMITH_API_URL", "https://api.smith.langchain.com"),
        api_key=os.getenv("LANGSMITH_API_KEY"),
    )


# Project configuration
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "langgraph-agent-template")
LANGSMITH_DATASET_PREFIX = os.getenv("LANGSMITH_DATASET_PREFIX", "template")

# Example dataset names (customize for your agent)
EXAMPLE_DATASET = f"{LANGSMITH_DATASET_PREFIX}-example"

# Example evaluation configurations (customize for your use case)
EVAL_CONFIG = {
    "example_threshold": 0.8,
}
