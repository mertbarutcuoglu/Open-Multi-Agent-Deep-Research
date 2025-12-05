"""Simple memory with automatic summarization of older turns."""

import asyncio
import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from deep_research.services.llm_service import LLMService
from deep_research.utils.session_id import get_session_id

# Roles
SYSTEM = "system"
ASSISTANT = "assistant"
USER = "user"
TOOL = "tool"

logger = logging.getLogger(__name__)

CURATOR_SYSTEM = (
    "You are a memory curator for a deep-research agent. "
    "Summarize earlier conversation into terse bullets under: Observations, Decisions, Follow-ups. "
    "Make sure to preserve the critical information needed for the initial task of the agent in your summaries"
    "No speculation, no credentials, no raw prompts."
)


def utc_iso(dt: Optional[datetime] = None) -> str:
    """Return an ISO-8601 UTC timestamp for ``dt`` or now."""
    return (dt or datetime.now(timezone.utc)).isoformat()


Msg = Dict[str, Any]
Rec = Dict[str, Any]  # {"msg": {...}, "meta": {...}}


@dataclass
class Memory:
    """
    Turn-bounded memory that:
      • Tracks full audit history (_history) with provenance.
      • Maintains model-facing messages (_messages) that auto-summarize older turns.
      • Summarizes once user_turns > max_turns, keeping the last keep_last_n_turns verbatim.
      • Summary is a synthetic user→assistant pair (NOT a strong system block).
    """

    agent_id: str
    llm: LLMService
    keep_last_n_turns: int = 5
    max_turns: int = 10
    session_id: Optional[str] = None
    autosave: bool = False
    autosave_every: int = 1

    _history: List[Rec] = field(default_factory=list, init=False, repr=False)
    _messages: List[Msg] = field(default_factory=list, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _autosave_counter: int = field(default=0, init=False, repr=False)

    # ------------------------- Public API -------------------------

    async def add_user_message(self, content: str) -> None:
        """Append a user message to memory and model-facing view."""
        await self._add(role=USER, content=content, kind="user_msg")

    async def add_assistant_message(self, content: str) -> None:
        """Append a plain assistant message (no tool calls)."""
        await self._add(role=ASSISTANT, content=content, kind="assistant_msg")

    async def add_assistant_message_with_tool_calls(
        self, tool_calls: List[Dict[str, Any]], content: str = ""
    ) -> None:
        """Append an assistant message that includes tool_calls metadata."""
        await self._add(
            role=ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            kind="assistant_tool_call",
        )

    async def add_tool_message(
        self, content: str, tool_call_id: str, name: Optional[str] = None
    ) -> None:
        """Append a tool result message tied to ``tool_call_id`` (optional ``name``)."""
        await self._add(
            role=TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            kind="tool_msg",
        )

    async def add_system_message(self, content: str) -> None:
        """Append a system directive message."""
        await self._add(role=SYSTEM, content=content, kind="system_prompt")

    async def get_model_messages(self) -> List[Msg]:
        """Return ready-to-send model messages (no metadata)."""
        async with self._lock:
            msgs = list(self._messages)
        return msgs

    async def save(self) -> str:
        """Persist history (messages + metadata) to ``output/<session>/<agent_id>/memory.json``."""
        sid = self.session_id or get_session_id()
        path = os.path.join("output", sid, self.agent_id, "memory.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with self._lock:
            payload = [
                {
                    "message": self._json_ready(dict(r["msg"])),
                    "metadata": self._json_ready(dict(r["meta"])),
                }
                for r in self._history
            ]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("Memory saved: %s", path)
        return path

    # ------------------------ Internals --------------------------

    async def _add(self, *, role: str, content: str, **meta: Any) -> None:
        """
        Append message with provenance into history, update model-facing view,
        and summarize if assistant-turn budget exceeded.
        Extra meta supported: tool_call_id, tool_calls, name, kind, who, when.
        """
        when = meta.pop("when", None) or utc_iso()
        who = meta.pop("who", None) or role

        # Build raw message
        msg: Msg = {"role": role, "content": content}
        # Tool message fields (tool_call_id/name) and assistant tool_calls (list)
        if "tool_call_id" in meta:
            msg["tool_call_id"] = meta["tool_call_id"]
        if "name" in meta and meta["name"] is not None:
            msg["name"] = meta["name"]
        if "tool_calls" in meta and meta["tool_calls"] is not None:
            msg["tool_calls"] = meta["tool_calls"]

        # Metadata (observability)
        meta_full: Dict[str, Any] = {
            "who": who,
            "when": when,
            "synthetic": False,
            **meta,  # keep kind/tool_call_id/tool_calls/name etc. for the audit log too
        }

        async with self._lock:
            self._history.append({"msg": msg, "meta": meta_full})
            # Mirror into _messages (model-facing)
            self._messages.append(self._sanitize_for_model(msg))

            need_summary, boundary = self._summarize_decision_locked()
            logger.debug(
                "Memory._add: role=%s need_summary=%s boundary=%s user_turns=%s total=%s",
                role,
                need_summary,
                boundary,
                self._count_user_turns_locked(),
                len(self._history),
            )

        if not need_summary:
            await self._autosave_if_enabled()
            return

        # Prepare prefix snapshot for the summarizer outside the lock
        async with self._lock:
            prefix_msgs = [
                r["msg"]
                for r in list(self._history)[:boundary]
                if (
                    r["msg"]["role"] != SYSTEM and r["msg"]["role"] != USER
                )  # Do not include the system and user message as they will be preserved as is
            ]

            assistant_summary = await self._summarize(prefix_msgs)

            snapshot = list(self._history)
            suffix_records = snapshot[boundary:]  # keep last N turns

            # Replace pre-boundary region by a synthetic pair (user → assistant)
            self._history.clear()
            self._history.append(snapshot[0])  # System prompt
            self._history.append(snapshot[1])  # User inquiry
            self._history.extend(
                [
                    {
                        "msg": {"role": ASSISTANT, "content": assistant_summary},
                        "meta": {
                            "synthetic": True,
                            "kind": "history_summary",
                            "summary_for_turns": f"< all before idx {boundary} >",
                            "who": "system/curator",
                            "when": utc_iso(),
                        },
                    },
                ]
            )
            self._history.extend(suffix_records)

            # Rebuild model-facing messages
            new_messages: List[Msg] = []

            # Suffix messages (keep as-is, model-safe) — avoid slicing a deque
            for i, rec in enumerate(self._history):
                new_messages.append(self._sanitize_for_model(rec["msg"]))

            self._messages = new_messages

        await self._autosave_if_enabled()

    # For observability
    async def _get_full_history(self) -> List[Dict[str, Any]]:
        """Return a deep copy-like list of all history records for observability."""
        return [
            {"message": dict(r["msg"]), "metadata": dict(r["meta"])}
            for r in self._history
        ]

    # ---- summarization helpers ----

    def _is_real_assistant_turn_start(self, rec: Rec) -> bool:
        """True if ``rec`` is a real (non-synthetic) assistant turn start."""
        return rec["msg"].get("role") == ASSISTANT and not rec["meta"].get(
            "synthetic", False
        )

    def _assistant_turn_starts_locked(self) -> List[int]:
        """Indices of assistant turn starts in ``_history`` (lock held)."""
        return [
            i
            for i, r in enumerate(self._history)
            if self._is_real_assistant_turn_start(r)
        ]

    def _count_user_turns_locked(self) -> int:
        """Count real assistant turns (proxy for user turns) with lock held."""
        return len(self._assistant_turn_starts_locked())

    def _summarize_decision_locked(self) -> Tuple[bool, int]:
        """Decide if summarization is needed; return (need_summary, boundary_idx)."""
        assistant_starts = self._assistant_turn_starts_locked()
        real_turns = len(assistant_starts)
        if real_turns <= self.max_turns:
            return False, -1
        if self.keep_last_n_turns == 0:
            return True, len(self._history)
        if real_turns < self.keep_last_n_turns:
            return False, -1
        boundary = assistant_starts[-self.keep_last_n_turns]
        if boundary <= 0:
            return False, -1
        return True, boundary

    async def _summarize(self, prefix_msgs: List[Msg]) -> str:
        """Summarize ``prefix_msgs`` via curator LLM; return assistant summary text."""
        clean_prefix = [self._sanitize_for_model(m) for m in prefix_msgs]
        req = [
            {"role": SYSTEM, "content": CURATOR_SYSTEM},
            {"role": USER, "content": self._format_for_curator(clean_prefix)},
        ]
        logger.debug("Summarizer: compressing %s messages", len(clean_prefix))
        try:
            summary_text = (await self.llm.generate_response(req)).strip()
        except Exception as e:
            logger.exception("Summarizer failed, falling back to stub: %s", e)
            summary_text = "Summary unavailable due to curator error."

        assistant_summary = (
            "[Summary of earlier turns. Treat this as prior context only.] \n"
            f"[History Summary @ {utc_iso()}]\n{summary_text}"
        )

        return assistant_summary

    # ---- utilities ----
    @staticmethod
    def _sanitize_for_model(msg: Msg) -> Msg:
        """
        Return a model-safe message. Pass-through fields needed by the OpenAI schema:
        - tool messages: tool_call_id, optional name
        - assistant messages with tool calls: tool_calls (list)
        """
        role = msg.get("role")
        if role not in (SYSTEM, ASSISTANT, USER, TOOL):
            role = ASSISTANT
        out: Msg = {"role": role, "content": msg.get("content", "")}
        # tool result
        if role == TOOL and "tool_call_id" in msg:
            out["tool_call_id"] = msg["tool_call_id"]
        if "name" in msg and msg["name"] is not None:
            out["name"] = msg["name"]
        # assistant tool calls
        if role == ASSISTANT and "tool_calls" in msg and msg["tool_calls"] is not None:
            out["tool_calls"] = msg["tool_calls"]
        return out

    @staticmethod
    def _format_for_curator(msgs: List[Msg]) -> str:
        """Flatten messages into a simple ROLE: content block for the curator."""
        parts: List[str] = []
        for m in msgs:
            role = m.get("role", "?").upper()
            content = (m.get("content") or "").strip()
            parts.append(f"{role}: {content}")
        return "\n\n".join(parts)

    @classmethod
    def _json_ready(cls, value: Any) -> Any:
        """Best-effort conversion of ``value`` to JSON-serializable primitives."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(k): cls._json_ready(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set, frozenset, deque)):
            return [cls._json_ready(v) for v in value]
        for attr in ("model_dump", "to_dict", "dict"):
            method = getattr(value, attr, None)
            if callable(method):
                try:
                    return cls._json_ready(method())
                except Exception:
                    pass
        if hasattr(value, "__dict__"):
            try:
                return cls._json_ready(vars(value))
            except Exception:
                pass
        return repr(value)

    async def _autosave_if_enabled(self) -> None:
        """Persist memory to disk when autosave is on and threshold reached."""
        if not self.autosave:
            return

        self._autosave_counter += 1
        if self._autosave_counter < max(1, self.autosave_every):
            return

        self._autosave_counter = 0
        try:
            await self.save()
        except Exception:
            logger.exception("Autosave failed")
