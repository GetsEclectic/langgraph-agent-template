"""
Utility for truncating only the most recent tool response when it is large.

Exports:
- make_recent_tool_response_summarizer(model, *, trigger_tokens=8000, summary_max_tokens=256)
  Returns a pre_model_hook callable suitable for LangGraph create_react_agent(..., pre_model_hook=...).

Behavior:
- If the last message in state["messages"] is a ToolMessage and exceeds trigger_tokens
  (using langchain-core's count_tokens_approximately), it is truncated deterministically:
  keep the first 4000 tokens and the last 4000 tokens (whitespace-delimited), inserting
  a clear marker indicating that the middle portion was removed.
- Only the last ToolMessage is replaced with its truncated content; the rest of the history is preserved.
- The hook returns {"llm_input_messages": new_messages} to avoid mutating stored history.

Notes:
- The "tokens" here are approximate and defined by whitespace-delimited chunks for speed and simplicity.
- The function signature is preserved; the model argument and summary_max_tokens are unused.
"""

import re
from typing import Any, List

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately


__all__ = ["make_recent_tool_response_summarizer"]


def make_recent_tool_response_summarizer(
    model: Any,
    *,
    trigger_tokens: int = 8000,
    summary_max_tokens: int = 256,
):
    """
    Create a pre_model_hook that truncates only the most recent ToolMessage if it is large.

    Parameters:
    - model: Preserved for compatibility; not used.
    - trigger_tokens: Threshold (approx tokens) at which the last ToolMessage is truncated.
    - summary_max_tokens: Preserved for compatibility; not used.

    Returns:
    - A callable(state: dict) -> dict, suitable for use as pre_model_hook.
    """

    HEAD_TOKENS = 4000
    TAIL_TOKENS = 4000

    def _truncate_head_tail(text: str) -> str:
        # Tokenize approximately by whitespace
        tokens = re.findall(r"\S+", text)
        total_tokens = len(tokens)

        if total_tokens <= HEAD_TOKENS + TAIL_TOKENS:
            return text

        head = " ".join(tokens[:HEAD_TOKENS])
        tail = " ".join(tokens[-TAIL_TOKENS:])
        omitted = max(total_tokens - HEAD_TOKENS - TAIL_TOKENS, 0)
        marker = f"\n\n[... {omitted} tokens omitted from the middle ...]\n\n"
        return f"{head}{marker}{tail}"

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
        truncated_text = _truncate_head_tail(raw_content).strip()
        if not truncated_text:
            return {"llm_input_messages": msgs}

        summarized_tool = ToolMessage(
            content=truncated_text,
            tool_call_id=last_tool.tool_call_id,  # preserve linkage to the original tool call
        )
        new_msgs = msgs[:-1] + [summarized_tool]
        return {"llm_input_messages": new_msgs}

    return _hook
