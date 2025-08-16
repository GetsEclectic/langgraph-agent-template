from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, AnyMessage

from agent.graph import make_graph


def _extract_text_from_message(msg: AnyMessage) -> str:
    """Robustly extract text content from a LangChain message."""
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    # content can be a list of content parts (dicts or pydantic models)
    try:
        parts = []
        for p in content:
            # Handle LC content parts with .type/.text or dicts
            if isinstance(p, dict):
                if "text" in p and isinstance(p["text"], str):
                    parts.append(p["text"])
                elif "content" in p and isinstance(p["content"], str):
                    parts.append(p["content"])
            else:
                txt = getattr(p, "text", None)
                if isinstance(txt, str):
                    parts.append(txt)
        return "\n".join(parts).strip()
    except Exception:
        return str(content)


def _extract_final_answer(state: Dict[str, Any]) -> str:
    """Extract the final answer text from agent state."""
    messages = state.get("messages", [])
    if not messages:
        return ""
    last: AnyMessage = messages[-1]
    if isinstance(last, AIMessage):
        return _extract_text_from_message(last).strip()
    # Fallback: search last AI message in reverse
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return _extract_text_from_message(msg).strip()
    return ""


class AgentTarget:
    """Wrapper around the agent graph used for evaluations."""

    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds
        self._graph = None

    async def __aenter__(self) -> "AgentTarget":
        self._graph = await make_graph()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # Nothing to clean up currently
        self._graph = None

    async def ainvoke(self, question: str, thread_id: Optional[str] = None) -> Dict[str, str]:
        """
        Invoke the agent graph on a single question and return formatted response.

        Returns:
            {"answer": str}
        """
        if self._graph is None:
            self._graph = await make_graph()

        if not thread_id:
            thread_id = str(uuid.uuid4())

        async def _call():
            state = await self._graph.ainvoke(
                {"messages": [("human", question)]},
                config={"configurable": {"thread_id": thread_id}},
            )
            answer = _extract_final_answer(state)
            return {"answer": answer}

        try:
            return await asyncio.wait_for(_call(), timeout=self.timeout_seconds)
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Agent invocation timed out after {self.timeout_seconds}s") from e
        except Exception:
            # Re-raise; caller handles
            raise


async def atarget(question: str, timeout_seconds: int = 60) -> Dict[str, str]:
    """Convenience async function to get answer for a question."""
    async with AgentTarget(timeout_seconds=timeout_seconds) as tgt:
        return await tgt.ainvoke(question)


def target(question: str, timeout_seconds: int = 60) -> Dict[str, str]:
    """Synchronous convenience wrapper."""
    return asyncio.run(atarget(question, timeout_seconds=timeout_seconds))
