from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional
import json
from dataclasses import dataclass

from langsmith import Client

import yaml


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


@dataclass
class ParsedDataset:
    name: Optional[str]
    description: str
    examples: List[Dict[str, Any]]
    judge_model: Optional[str] = None


def parse_dataset_yaml(file_path: str) -> ParsedDataset:
    """Parse a YAML file describing a dataset of examples.

    Supported formats:
    - Object with keys: name, description, examples
    - Object with key: dataset: { name, description, examples }
    - Top-level list of examples (name will be None)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    name: Optional[str] = None
    description: str = ""
    examples: List[Dict[str, Any]]
    judge_model: Optional[str] = None

    obj = data
    if isinstance(data, dict) and "dataset" in data and isinstance(data["dataset"], dict):
        obj = data["dataset"]

    if isinstance(obj, dict):
        name = obj.get("name")
        description = obj.get("description", "")
        examples = obj.get("examples", [])
        judge_model = obj.get("judge_model") or data.get("judge_model")
    elif isinstance(obj, list):
        examples = obj
    else:
        raise ValueError("Unsupported dataset YAML format")

    if not isinstance(examples, list):
        raise ValueError("'examples' must be a list of objects with 'inputs' and 'outputs'")

    # Basic validation/normalization
    normalized: List[Dict[str, Any]] = []
    for ex in examples:
        if not isinstance(ex, dict):
            raise ValueError("Each example must be an object")
        if "inputs" not in ex or "outputs" not in ex:
            raise ValueError("Each example must contain 'inputs' and 'outputs'")
        normalized.append({"inputs": ex["inputs"], "outputs": ex["outputs"]})

    return ParsedDataset(name=name, description=description, examples=normalized, judge_model=judge_model)


def ensure_dataset_with_examples(
    client: Client,
    *,
    name: str,
    description: str = "",
    examples: List[Dict[str, Any]],
) -> Tuple[Any, int]:
    """Create or get a dataset by name and ensure examples exist; dedupe by inputs.

    Returns: (dataset, num_removed_duplicates)
    """
    ds = get_or_create_dataset(client, name, description=description)
    removed = dedupe_examples_by_inputs(client, ds.id)
    ensure_examples(client, ds.id, examples)
    return ds, removed
