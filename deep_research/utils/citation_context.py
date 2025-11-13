"""Utilities for preparing context for the citation agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from deep_research.utils.output_parser import OUTPUT_DIR


@dataclass(frozen=True)
class CitationArtifact:
    """Container for a supporting research artifact."""

    name: str
    content: str


@dataclass(frozen=True)
class CitationContext:
    """Context payload for the citation agent."""

    session_id: str
    final_report: str
    research_plan: Optional[str]
    artifacts: List[CitationArtifact]


def _load_text_if_exists(path: Path) -> Optional[str]:
    """Return file contents if ``path`` exists; otherwise ``None``.

    The file is read as UTF-8. This helper avoids raising when an optional
    artifact (e.g., research_plan.md) is absent.
    """
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def load_citation_context(session_id: str) -> CitationContext:
    """Load the final report and supporting artifacts for ``session_id``."""

    session_dir = OUTPUT_DIR / session_id
    if not session_dir.is_dir():
        raise FileNotFoundError(
            f"Session directory not found for id '{session_id}': {session_dir}"
        )

    report_path = session_dir / "report.md"
    final_report = _load_text_if_exists(report_path)
    if final_report is None:
        raise FileNotFoundError(
            f"Final report not found for session '{session_id}': {report_path}"
        )

    research_plan = _load_text_if_exists(session_dir / "research_plan.md")

    artifact_paths = sorted(
        path
        for path in session_dir.glob("*.md")
        if path.name not in {"report.md", "research_plan.md"}
    )

    artifacts = [
        CitationArtifact(name=path.name, content=path.read_text(encoding="utf-8"))
        for path in artifact_paths
    ]

    return CitationContext(
        session_id=session_id,
        final_report=final_report,
        research_plan=research_plan,
        artifacts=artifacts,
    )


def build_citation_agent_message(context: CitationContext) -> str:
    """Create the initial instruction message for the citation agent."""

    lines: List[str] = []
    lines.append(
        "You are a meticulous research editor. The lead researcher has finished a draft "
        "report for the user. Revise it so that every verifiable fact is supported by "
        "inline citations that point to the provided artifacts."
    )
    lines.append(
        "Your deliverable is the revised report only. Preserve the structure and claims, "
        "tighten wording if needed, and insert bracketed numeric citations like [1], [2]."
    )
    lines.append(
        "Do not invent new facts or sources. Cite only from the supplied artifacts and "
        "list each citation in a final 'Sources' section with the matching number and URL "
        "or document reference."
    )
    lines.append(
        "After verifying the report, return the updated markdown that already includes "
        "the citations and the sources section."
    )

    if context.research_plan:
        lines.append(
            "\nResearch plan (for context only – cite from it only if it contains explicit sources):"
        )
        lines.append("```markdown")
        lines.append(context.research_plan.strip())
        lines.append("```")

    lines.append("\nDraft final report from the lead researcher:")
    lines.append("```markdown")
    lines.append(context.final_report.strip())
    lines.append("```")

    if context.artifacts:
        lines.append("\nSupporting artifacts with evidence:")
        for idx, artifact in enumerate(context.artifacts, start=1):
            lines.append(f"--- Artifact {idx}: {artifact.name} ---")
            lines.append("```markdown")
            lines.append(artifact.content.strip())
            lines.append("```")
    else:
        lines.append(
            "\nNo additional artifacts were saved for this session. Use only the final report "
            "and research plan when citing."
        )

    return "\n".join(lines)
