from __future__ import annotations

from typing import Any, Dict, List, Tuple
import json

from langsmith import Client

from .config import LANGSMITH_DATASET_PREFIX

# Dataset names
FILESYSTEM_DATASET = f"{LANGSMITH_DATASET_PREFIX}-filesystem"

# Single example from the plan
FILESYSTEM_EXAMPLES: List[Dict[str, Dict[str, str]]] = [
    {
        "inputs": {"question": "can you list all the files in the project root?"},
        "outputs": {"answer": """Here are all the files and directories in the project root (`/app`):

**Files:**
- `README.md` - Project documentation
- `langgraph.json` - LangGraph configuration file
- `pyproject.toml` - Python project configuration

**Directories:**
- `agent/` - Contains the agent implementation
- `infra/` - Infrastructure-related files
- `project_root/` - Additional project files
- `scripts/` - Utility scripts"""},
    },
]


def get_or_create_dataset(client: Client, name: str, description: str = ""):
    """Idempotently get or create a dataset by name."""
    try:
        ds = client.read_dataset(dataset_name=name)
        return ds
    except Exception:
        return client.create_dataset(dataset_name=name, description=description)


def _examples_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    # Consider examples equal if their inputs match. Outputs can change due to formatting or evaluator updates.
    return a.get("inputs") == b.get("inputs")


def ensure_examples(client: Client, dataset_id: str, examples: List[Dict[str, Any]]) -> int:
    """Ensure the provided examples exist in the dataset. Returns number of examples added."""
    existing = list(client.list_examples(dataset_id=dataset_id))
    to_add = []
    for ex in examples:
        if not any(_examples_equal({"inputs": e.inputs, "outputs": e.outputs}, ex) for e in existing):
            to_add.append(ex)

    for ex in to_add:
        client.create_example(
            inputs=ex["inputs"],
            outputs=ex["outputs"],
            dataset_id=dataset_id,
        )

    return len(to_add)


def dedupe_examples_by_inputs(client: Client, dataset_id: str) -> int:
    """Remove duplicate examples with the same inputs, keeping the first occurrence."""
    existing = list(client.list_examples(dataset_id=dataset_id))
    seen = set()
    to_delete = []
    for e in existing:
        try:
            key = json.dumps(e.inputs, sort_keys=True)
        except Exception:
            key = str(e.inputs)
        if key in seen:
            to_delete.append(e.id)
        else:
            seen.add(key)
    for ex_id in to_delete:
        try:
            client.delete_example(example_id=ex_id)
        except Exception:
            # Best-effort; continue
            pass
    return len(to_delete)


def ensure_filesystem_dataset(client: Client) -> Tuple[Any, int]:
    """Create the filesystem dataset and add examples idempotently; also deduplicate by inputs.

    Returns:
        (dataset, num_removed_duplicates)
    """
    ds = get_or_create_dataset(
        client,
        FILESYSTEM_DATASET,
        description="Evaluation dataset for agent questions about the filesystem.",
    )
    removed = dedupe_examples_by_inputs(client, ds.id)
    ensure_examples(client, ds.id, FILESYSTEM_EXAMPLES)
    return ds, removed
