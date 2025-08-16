from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence, Union

from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

# Type aliases for clarity
EvaluatorResult = Dict[str, Any]
SimpleEvaluator = Callable[..., Union[EvaluatorResult, Sequence[EvaluatorResult]]]


def create_correctness_evaluator(
    *,
    model: str = "anthropic:claude-3-5-sonnet-latest",
    feedback_key: str = "correctness",
    continuous: bool = False,
    choices: Optional[Sequence[float]] = None,
) -> SimpleEvaluator:
    """
    Create an LLM-as-judge evaluator for correctness using OpenEvals.

    Args:
        model: Judge model spec (provider:model). Requires corresponding LangChain integration.
               Default uses Anthropic Sonnet; set ANTHROPIC_API_KEY in env.
        feedback_key: Feedback key name to log to LangSmith.
        continuous: If True, returns a float score in [0,1] instead of boolean.
        choices: Optional discrete choice scores; mutually exclusive with `continuous`.

    Returns:
        A callable evaluator(inputs=..., outputs=..., reference_outputs=...)
        that returns an EvaluatorResult dict or list of dicts.
    """
    kwargs: Dict[str, Any] = {
        "prompt": CORRECTNESS_PROMPT,
        "feedback_key": feedback_key,
        "model": model,
    }
    if choices is not None:
        kwargs["choices"] = list(choices)
    else:
        kwargs["continuous"] = continuous

    evaluator = create_llm_as_judge(**kwargs)

    def wrapped(
        *,
        inputs: Any,
        outputs: Any,
        reference_outputs: Any,
        **_: Any,
    ) -> Union[EvaluatorResult, Sequence[EvaluatorResult]]:
        # Pass through to OpenEvals evaluator
        return evaluator(
            inputs=inputs,
            outputs=outputs,
            reference_outputs=reference_outputs,
        )

    return wrapped


# Default convenience factory
def get_default_evaluators() -> Sequence[SimpleEvaluator]:
    """
    Return the default list of evaluators for our first experiment.
    Currently includes a correctness evaluator (binary).
    """
    return [create_correctness_evaluator()]
