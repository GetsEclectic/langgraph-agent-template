from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from langsmith import Client

from .config import LANGSMITH_PROJECT, get_langsmith_client
from .datasets import ensure_filesystem_dataset
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


def run_filesystem_evaluation(
    *,
    judge_model: str = "anthropic:claude-3-5-sonnet-latest",
    experiment_prefix: str = "filesystem",
    dataset_name: Optional[str] = None,
    continuous: bool = False,
    choices: Optional[List[float]] = None,
    project_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orchestrate the full evaluation run for the filesystem question.

    Args:
        judge_model: LLM-as-judge model (provider:model). Default Anthropc Sonnet.
        experiment_prefix: Prefix for LangSmith experiment.
        dataset_name: Optional override dataset name. Defaults to FILESYSTEM_DATASET.
        continuous: If True, evaluator returns float score in [0,1].
        choices: Optional discrete scores list; mutually exclusive with 'continuous'.
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

    # Ensure dataset exists with the single example and dedupe by inputs
    ds, removed = ensure_filesystem_dataset(client)
    ds_name = dataset_name or ds.name
    if removed:
        warnings.append(
            f"Removed {removed} duplicate example(s) with the same inputs from dataset '{ds_name}'."
        )

    # Build evaluators
    evaluator = create_correctness_evaluator(
        model=judge_model, continuous=continuous, choices=choices
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
