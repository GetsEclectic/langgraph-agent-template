from __future__ import annotations

import os
from typing import Any, Dict, Optional

from langsmith import Client

from .config import LANGSMITH_PROJECT, get_langsmith_client
from .datasets import (
    ensure_dataset_with_examples,
    parse_dataset_yaml,
)
from .evaluators import create_correctness_evaluator
from .target import target as agent_target


def _ensure_tracing_env() -> None:
    # Best-effort enable LangSmith tracing if not already set
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)


def _validate_env() -> List[str]:
    missing: List[str] = []
    if not os.getenv("LANGSMITH_API_KEY"):
        missing.append("LANGSMITH_API_KEY")
    if not os.getenv("ANTHROPIC_API_KEY"):
        # Required for both agent (ChatAnthropic) and evaluator default model
        missing.append("ANTHROPIC_API_KEY")
    return missing


def _make_target_wrapper():
    """
    Wrap the agent target to accept LangSmith dataset 'inputs' dict.

    Dataset inputs are expected to be of the form: {"question": "..."}
    Returns a dict like: {"answer": "..."}
    """

    def _wrapped(inputs: Dict[str, Any]) -> Dict[str, str]:
        question = inputs.get("question", "")
        try:
            return agent_target(question)
        except Exception as e:
            # Ensure evaluation completes and logs a result even if the target errors.
            # Return a structured fallback so evaluators can still run.
            return {"answer": f"[error] {e.__class__.__name__}: {str(e)}"}

    return _wrapped


def run_evaluation(
    *,
    dataset_file: str,
    experiment_prefix: str = "eval",
    project_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orchestrate a generic evaluation run using a YAML dataset file.

    Args:
        dataset_file: Path to YAML file describing dataset examples.
        experiment_prefix: Prefix for LangSmith experiment.
        project_name: Optional override of LangSmith project name.

    Returns:
        A dict with keys:
          - "experiment_name"
          - "dataset_name"
          - "project_name"
          - "result" (LangSmith evaluation result object)
          - "warnings" (list of strings)
    """
    _ensure_tracing_env()
    warnings = []
    missing = _validate_env()
    if missing:
        warnings.append(
            f"Missing required environment variables: {', '.join(missing)}. "
            "The evaluation may fail to authenticate."
        )

    client: Client = get_langsmith_client()

    # Parse dataset YAML and ensure dataset/examples exist
    parsed = parse_dataset_yaml(dataset_file)
    derived_name = parsed.name
    if not derived_name:
        raise ValueError("Dataset YAML must include a 'name' field under 'dataset'.")

    ds, removed = ensure_dataset_with_examples(
        client,
        name=derived_name,
        description=parsed.description or "Evaluation dataset",
        examples=parsed.examples,
    )
    ds_name = ds.name
    if removed:
        warnings.append(
            f"Removed {removed} duplicate example(s) with the same inputs from dataset '{ds_name}'."
        )

    # Build evaluators
    evaluator = create_correctness_evaluator(
        model=parsed.judge_model or "anthropic:claude-3-5-sonnet-latest"
    )
    evaluators = [evaluator]

    # Build target wrapper
    target_fn = _make_target_wrapper()

    # Run evaluation
    # Note: project_name defaults to LANGSMITH_PROJECT if not provided
    result = client.evaluate(
        target_fn,
        data=ds_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        error_handling="log",
    )

    return {
        "experiment_name": getattr(result, "name", experiment_prefix),
        "dataset_name": ds_name,
        "project_name": project_name or LANGSMITH_PROJECT,
        "result": result,
        "warnings": warnings,
    }
