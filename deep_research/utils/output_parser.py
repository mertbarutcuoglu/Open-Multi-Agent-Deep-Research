"""Utilities for reading generated research artifacts.

The Deep Search agent stores all run outputs inside ``output/<session_id>``
directories. This module exposes focused helpers that surface the main
research deliverables (plan, report, and sub-reports) for downstream tooling
such as evaluations.
"""

from pathlib import Path
from typing import List

# All session artifacts live under the project-level output/ directory.
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def _get_session_dir(session_id: str) -> Path:
    """Return the directory that holds the outputs for ``session_id``."""

    session_dir = OUTPUT_DIR / session_id
    if not session_dir.is_dir():
        raise FileNotFoundError(
            f"Session directory not found for id '{session_id}': {session_dir}"
        )
    return session_dir


def _read_file(file_path: Path) -> str:
    """Read ``file_path`` as UTF-8, raising if the file does not exist."""

    if not file_path.is_file():
        raise FileNotFoundError(f"Expected file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


def get_research_plan(session_id: str) -> str:
    """
    Locate ``research_plan.md`` for ``session_id`` and return its contents.

    Raises:
        FileNotFoundError: If the session directory or file does not exist.
    """

    session_dir = _get_session_dir(session_id)
    return _read_file(session_dir / "research_plan.md")


def get_report(session_id: str) -> str:
    """
    Locate ``report.md`` for ``session_id`` and return its contents.

    Raises:
        FileNotFoundError: If the session directory or file does not exist.
    """

    session_dir = _get_session_dir(session_id)
    return _read_file(session_dir / "report.md")


def get_sub_reports(session_id: str) -> List[str]:
    """
    Collect all sub-report markdown files for ``session_id``.

    Sub-reports are the markdown files inside the session directory other than
    ``report.md`` and ``research_plan.md``. The returned list is sorted by
    filename to keep the output deterministic.

    Raises:
        FileNotFoundError: If the session directory does not exist.
    """

    session_dir = _get_session_dir(session_id)
    sub_report_paths = sorted(
        path
        for path in session_dir.glob("*.md")
        if path.name not in {"report.md", "research_plan.md"}
    )
    return [_read_file(path) for path in sub_report_paths]
