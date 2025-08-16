#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure project root is on sys.path when invoked directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from infra.langsmith.runner import run_evaluation  # noqa: E402


def _print_env_summary() -> None:
    console = Console()
    table = Table(title="Environment Summary")
    table.add_column("Variable", style="cyan")
    table.add_column("Value", style="magenta")
    for var in ["LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "LANGSMITH_TRACING", "ANTHROPIC_API_KEY"]:
        val = os.getenv(var)
        display = "***set***" if val else "(missing)"
        if var == "LANGSMITH_PROJECT":
            display = val or "(default: langgraph-agent-template)"
        if var == "LANGSMITH_TRACING":
            display = val or "(default: true)"
        table.add_row(var, display)
    console.print(table)


def main(
    dataset_file: str = typer.Option(
        ...,  # required
        "--dataset-file",
        help="Path to YAML file containing dataset examples.",
    ),
    experiment_prefix: str = typer.Option(
        "eval",
        "--experiment-prefix",
        help="Prefix to use for the LangSmith experiment name.",
    ),
    project_name: Optional[str] = typer.Option(
        None,
        "--project-name",
        help="Override LangSmith project name (defaults to env LANGSMITH_PROJECT or project default).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print raw JSON result instead of formatted output.",
    ),
):
    """
    Run a generic evaluation using a YAML dataset file and validate correctness against the expected answer.
    """
    _print_env_summary()

    result = run_evaluation(
        dataset_file=dataset_file,
        experiment_prefix=experiment_prefix,
        project_name=project_name,
    )

    if json_output:
        print(json.dumps(
            {
                "experiment_name": result.get("experiment_name"),
                "dataset_name": result.get("dataset_name"),
                "project_name": result.get("project_name"),
                "warnings": result.get("warnings", []),
            },
            indent=2,
        ))
        return

    warnings = result.get("warnings") or []
    if warnings:
        rprint(Panel.fit("\n".join(warnings), title="Warnings", border_style="yellow"))

    rprint(Panel.fit(
        f"Experiment: [bold]{result.get('experiment_name')}[/bold]\n"
        f"Dataset: [bold]{result.get('dataset_name')}[/bold]\n"
        f"Project: [bold]{result.get('project_name')}[/bold]\n",
        title="LangSmith Evaluation Started",
        border_style="green",
    ))
    rprint("Visit LangSmith to view detailed results and feedback once the run completes.")


if __name__ == "__main__":
    typer.run(main)
