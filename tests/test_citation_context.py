from pathlib import Path

import pytest

from deep_research.utils import citation_context
from deep_research.utils import output_parser


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_citation_context_reads_expected_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(citation_context, "OUTPUT_DIR", tmp_path)

    session_id = "session_citations"
    session_dir = tmp_path / session_id
    session_dir.mkdir()

    _write(session_dir / "report.md", "Report body")
    _write(session_dir / "research_plan.md", "Plan text")
    _write(session_dir / "sub_report_a.md", "Content A")
    _write(session_dir / "notes.txt", "Ignore me")
    _write(session_dir / "sub_report_b.md", "Content B")

    ctx = citation_context.load_citation_context(session_id)

    assert ctx.final_report == "Report body"
    assert ctx.research_plan == "Plan text"
    artifact_names = [artifact.name for artifact in ctx.artifacts]
    assert artifact_names == ["sub_report_a.md", "sub_report_b.md"]


def test_load_citation_context_missing_report_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(citation_context, "OUTPUT_DIR", tmp_path)
    session_id = "missing_report"
    session_dir = tmp_path / session_id
    session_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        citation_context.load_citation_context(session_id)


def test_build_citation_agent_message_includes_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(citation_context, "OUTPUT_DIR", tmp_path)

    session_id = "session_message"
    session_dir = tmp_path / session_id
    session_dir.mkdir()

    _write(session_dir / "report.md", "# Draft\nFinding")
    _write(session_dir / "research_plan.md", "Plan goes here")
    _write(session_dir / "sub_report_a.md", "Evidence one")

    ctx = citation_context.load_citation_context(session_id)
    message = citation_context.build_citation_agent_message(ctx)

    assert "Draft final report" in message
    assert "Supporting artifacts" in message
    assert "Plan goes here" in message
    assert "Evidence one" in message
