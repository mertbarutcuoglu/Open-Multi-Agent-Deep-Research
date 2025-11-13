from pathlib import Path

import pytest

from deep_research.utils import output_parser


def _prepare_session(base_dir: Path, session_id: str) -> Path:
    session_dir = base_dir / session_id
    session_dir.mkdir()
    return session_dir


def test_get_research_plan_returns_file_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    session_id = "session_plan"
    session_dir = _prepare_session(tmp_path, session_id)
    plan_text = "Plan details"
    (session_dir / "research_plan.md").write_text(plan_text, encoding="utf-8")
    (session_dir / "report.md").write_text("Report body", encoding="utf-8")

    assert output_parser.get_research_plan(session_id) == plan_text


def test_get_report_returns_file_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    session_id = "session_report"
    session_dir = _prepare_session(tmp_path, session_id)
    (session_dir / "research_plan.md").write_text("Plan", encoding="utf-8")
    report_text = "Main report"
    (session_dir / "report.md").write_text(report_text, encoding="utf-8")

    assert output_parser.get_report(session_id) == report_text


def test_get_sub_reports_returns_all_markdown_except_plan_and_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    session_id = "session_sub_reports"
    session_dir = _prepare_session(tmp_path, session_id)
    (session_dir / "research_plan.md").write_text("Plan", encoding="utf-8")
    (session_dir / "report.md").write_text("Report", encoding="utf-8")
    sub_a = session_dir / "sub_report_a.md"
    sub_b = session_dir / "sub_report_b.md"
    (session_dir / "notes.txt").write_text("Ignore", encoding="utf-8")
    sub_a.write_text("Sub A", encoding="utf-8")
    sub_b.write_text("Sub B", encoding="utf-8")

    assert output_parser.get_sub_reports(session_id) == ["Sub A", "Sub B"]


def test_missing_session_directory_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        output_parser.get_report("unknown_session")


def test_missing_expected_file_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(output_parser, "OUTPUT_DIR", tmp_path)
    session_id = "session_missing_file"
    _prepare_session(tmp_path, session_id)

    with pytest.raises(FileNotFoundError):
        output_parser.get_research_plan(session_id)
