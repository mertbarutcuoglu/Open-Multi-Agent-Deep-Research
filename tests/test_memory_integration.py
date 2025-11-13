import types
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

import pytest

fake_litellm = types.SimpleNamespace()


async def _fake_acompletion(**kwargs: Any) -> Dict[str, Any]:
    return {"choices": [{"message": {"content": "test"}}]}


fake_litellm.acompletion = _fake_acompletion
sys.modules.setdefault("litellm", fake_litellm)


from deep_research.utils.memory import Memory  # noqa: E402


class FakeLLM:
    """Minimal async stub of LLMService that returns a deterministic summary."""

    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        return "Observations: • prior context summarized.\nDecisions: • none.\nFollow-ups: • none."


@pytest.mark.asyncio
async def test_tool_call_roundtrip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Assistant tool_calls followed by tool result should be preserved in model messages."""
    import deep_research.utils.session_id as session_mod

    monkeypatch.setattr(session_mod, "get_session_id", lambda: "tools1")

    mem = Memory(
        agent_id="agentT",
        llm=FakeLLM(),
        keep_last_n_turns=3,
        max_turns=3,
        session_id="tools1",
    )

    await mem.add_system_message("You are a helpful deep-research agent.")
    await mem.add_user_message("Find X")

    tool_calls = [
        {
            "id": "call_123",
            "type": "function",
            "function": {"name": "search", "arguments": '{"q":"X"}'},
        }
    ]
    await mem.add_assistant_message_with_tool_calls(tool_calls, content="")
    await mem.add_tool_message(
        content="RESULT_X", tool_call_id="call_123", name="search"
    )

    msgs = await mem.get_model_messages()
    # Expect last two are assistant with tool_calls then tool message
    assert msgs[-2]["role"] == "assistant"
    assert "tool_calls" in msgs[-2] and msgs[-2]["tool_calls"][0]["id"] == "call_123"
    assert msgs[-1]["role"] == "tool"
    assert msgs[-1]["tool_call_id"] == "call_123"
    assert msgs[-1].get("name") == "search"
    assert msgs[-1]["content"] == "RESULT_X"

    # Save should persist metadata including tool_call_id
    save_path = await mem.save()
    data = json.loads(Path(save_path).read_text(encoding="utf-8"))
    # The last record in history should include tool_call_id in either message or metadata
    assert any(
        (
            r.get("message", {}).get("role") == "tool"
            and r["message"].get("tool_call_id") == "call_123"
        )
        for r in data
    )


@pytest.mark.asyncio
async def test_summarization_with_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    With keep_last_n_turns=2 and max_turns=3:
    - Build turns where the first user turn includes a tool call & result.
    - After adding 4th assistant turn, the first turn (with tool traffic) is summarized away.
    - Suffix should keep turns 3 and 4 verbatim.
    """
    import deep_research.utils.session_id as session_mod

    monkeypatch.setattr(session_mod, "get_session_id", lambda: "tools2")

    mem = Memory(
        agent_id="agentS",
        llm=FakeLLM(),
        keep_last_n_turns=2,
        max_turns=3,
        session_id="tools2",
    )

    await mem.add_system_message("sys")
    await mem.add_user_message("u1")

    # Turn 1
    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_a",
                "type": "function",
                "function": {"name": "lookup", "arguments": '{"k":"v"}'},
            }
        ],
        content="a1",
    )
    await mem.add_tool_message("tool_a", tool_call_id="call_a", name="lookup")

    # Turn 2
    await mem.add_assistant_message("a2")
    await mem.add_tool_message("tool_a", tool_call_id="call_a", name="lookup")
    await mem.add_tool_message("tool_a", tool_call_id="call_a", name="lookup")

    # Turn 3
    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_a",
                "type": "function",
                "function": {"name": "lookup", "arguments": '{"k":"v"}'},
            }
        ],
        content="a3",
    )
    await mem.add_tool_message("tool_b", tool_call_id="call_b", name="lookup")

    # Trigger summary with 4th assistant turn
    await mem.add_assistant_message("a4")

    model_msgs = await mem.get_model_messages()
    # 0: latest system prior to boundary
    assert model_msgs[0]["role"] == "system" and model_msgs[0]["content"] == "sys"
    assert model_msgs[1]["role"] == "user" and model_msgs[1]["content"] == "u1"
    assert model_msgs[2]["role"] == "assistant" and model_msgs[2]["content"].startswith(
        "[Summary of earlier turns"
    )

    # The suffix should include last 2 *turns*: u3,a3,u4  (assistant after u4 hasn't been appended yet)
    tail = model_msgs[-3:]
    assert [m["role"] for m in tail] == ["assistant", "tool", "assistant"]
    assert [m["content"] for m in tail] == ["a3", "tool_b", "a4"]

    # The earlier tool messages (u1 turn) are summarized away and should not appear in suffix
    assert not any(
        m.get("tool_call_id") == "call_a" for m in model_msgs[3:]
    )  # after summary pair

    # Observability history should mark the first entry as synthetic
    hist = await mem._get_full_history()
    assert hist[2]["metadata"]["synthetic"] is True


@pytest.mark.asyncio
async def test_double_summarization_with_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Ensure multiple summarizations continue to drop the oldest tool traffic while keeping
    only the latest keep_last_n_turns verbatim after each summarization pass.
    """
    import deep_research.utils.session_id as session_mod

    monkeypatch.setattr(session_mod, "get_session_id", lambda: "tools2_double")

    mem = Memory(
        agent_id="agentS2",
        llm=FakeLLM(),
        keep_last_n_turns=2,
        max_turns=3,
        session_id="tools2_double",
    )

    await mem.add_system_message("sys")
    await mem.add_user_message("u1")

    # First block of turns; the 4th assistant turn will trigger the first summary.
    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_a",
                "type": "function",
                "function": {"name": "lookup", "arguments": '{"k":"v"}'},
            }
        ],
        content="a1",
    )
    await mem.add_tool_message("tool_a", tool_call_id="call_a", name="lookup")

    await mem.add_assistant_message("a2")
    await mem.add_tool_message("tool_a_2", tool_call_id="call_a", name="lookup")

    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_b",
                "type": "function",
                "function": {"name": "lookup", "arguments": '{"k":"v"}'},
            }
        ],
        content="a3",
    )
    await mem.add_tool_message("tool_b", tool_call_id="call_b", name="lookup")

    await mem.add_assistant_message("a4")  # triggers first summary

    msgs_after_first_summary = await mem.get_model_messages()
    assert [m["content"] for m in msgs_after_first_summary[-3:]] == [
        "a3",
        "tool_b",
        "a4",
    ]

    # Second block of turns; the 6th assistant turn triggers another summary.
    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_c",
                "type": "function",
                "function": {"name": "lookup", "arguments": '{"k":"v"}'},
            }
        ],
        content="a5",
    )
    await mem.add_tool_message("tool_c", tool_call_id="call_c", name="lookup")

    await mem.add_assistant_message("a6")  # triggers second summary

    model_msgs = await mem.get_model_messages()
    assert model_msgs[0]["role"] == "system" and model_msgs[0]["content"] == "sys"
    assert model_msgs[1]["role"] == "user" and model_msgs[1]["content"] == "u1"
    assert model_msgs[2]["role"] == "assistant"
    assert model_msgs[2]["content"].startswith("[Summary of earlier turns")

    tail = model_msgs[-3:]
    assert [m["role"] for m in tail] == ["assistant", "tool", "assistant"]
    assert [m["content"] for m in tail] == ["a5", "tool_c", "a6"]

    # Tool traffic from the first block should have been summarized away.
    assert not any(m.get("tool_call_id") == "call_a" for m in model_msgs[3:])
    assert not any(m.get("tool_call_id") == "call_b" for m in model_msgs[3:])

    hist = await mem._get_full_history()
    assert hist[2]["metadata"]["synthetic"] is True
    real_assistant_msgs = [
        rec["message"]["content"]
        for rec in hist
        if rec["message"]["role"] == "assistant"
        and not rec["metadata"].get("synthetic")
    ]
    assert real_assistant_msgs == ["a5", "a6"]


@pytest.mark.asyncio
async def test_save_persists_tool_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    Ensure saved history includes tool metadata (tool_call_id/name) for auditability.
    """
    import deep_research.utils.session_id as session_mod

    monkeypatch.setattr(session_mod, "get_session_id", lambda: "persisttools")

    mem = Memory(
        agent_id="agentP",
        llm=FakeLLM(),
        keep_last_n_turns=3,
        max_turns=3,
        session_id="persisttools",
    )

    await mem.add_system_message("sys")
    await mem.add_user_message("u1")
    await mem.add_assistant_message_with_tool_calls(
        [
            {
                "id": "call_xyz",
                "type": "function",
                "function": {"name": "calc", "arguments": '{"a":1}'},
            }
        ],
        content="",
    )
    await mem.add_tool_message(content="42", tool_call_id="call_xyz", name="calc")

    save_path = await mem.save()
    data = json.loads(Path(save_path).read_text(encoding="utf-8"))

    tool_recs = [r for r in data if r["message"]["role"] == "tool"]
    assert len(tool_recs) == 1
    assert tool_recs[0]["message"]["tool_call_id"] == "call_xyz"
    assert tool_recs[0]["message"].get("name") == "calc"
