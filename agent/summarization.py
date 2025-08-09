"""
Utility for summarizing only the most recent tool response when it is large.

Exports:
- make_recent_tool_response_summarizer(model, *, trigger_tokens=8000, summary_max_tokens=256)
  Returns a pre_model_hook callable suitable for LangGraph create_react_agent(..., pre_model_hook=...).

Behavior:
- If the last message in state["messages"] is a ToolMessage and exceeds trigger_tokens
  (using langchain-core's count_tokens_approximately), it is summarized via the provided model.
- Only the last ToolMessage is replaced with its summary; the rest of the history is preserved.
- The hook returns {"llm_input_messages": new_messages} to avoid mutating stored history.
"""

from typing import Any, List

from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately


__all__ = ["make_recent_tool_response_summarizer"]


def make_recent_tool_response_summarizer(
    model: Any,
    *,
    trigger_tokens: int = 8000,
    summary_max_tokens: int = 256,
):
    """
    Create a pre_model_hook that summarizes only the most recent ToolMessage if it is large.

    Parameters:
    - model: A LangChain chat model with .invoke([...]) support.
    - trigger_tokens: Threshold (approx tokens) at which the last ToolMessage is summarized.
    - summary_max_tokens: Target size for the summary (enforced via prompt instruction).

    Returns:
    - A callable(state: dict) -> dict, suitable for use as pre_model_hook.
    """

    def _summarize_text_via_llm(text: str) -> str:
        prompt_messages = [
            SystemMessage(
                content=(
                    "You are a precise summarizer. Produce a concise, faithful "
                    "summary of the tool output, preserving key results, errors, "
                    "identifiers, paths, and any actionable items. Do not invent details."
                )
            ),
            HumanMessage(
                content=(
                    f"Summarize the following tool output in at most {summary_max_tokens} tokens:\n\n{text}"
                )
            ),
        ]
        result = model.invoke(prompt_messages)
        content = result.content
        return content if isinstance(content, str) else str(content)

    def _hook(state: dict) -> dict:
        msgs: List[BaseMessage] = state.get("messages", [])
        if not msgs or not isinstance(msgs[-1], ToolMessage):
            return {"llm_input_messages": msgs}

        last_tool: ToolMessage = msgs[-1]
        tool_tokens = count_tokens_approximately([last_tool])

        if tool_tokens <= trigger_tokens:
            return {"llm_input_messages": msgs}

        raw_content = (
            last_tool.content if isinstance(last_tool.content, str) else str(last_tool.content)
        )
        summary_text = _summarize_text_via_llm(raw_content).strip()
        if not summary_text:
            return {"llm_input_messages": msgs}

        summarized_tool = ToolMessage(
            content=summary_text,
            tool_call_id=last_tool.tool_call_id,  # preserve linkage to the original tool call
        )
        new_msgs = msgs[:-1] + [summarized_tool]
        return {"llm_input_messages": new_msgs}

    return _hook
