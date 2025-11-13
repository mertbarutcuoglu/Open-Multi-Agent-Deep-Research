"""LLM-as-judge evals for Deep Research outputs using DeepEval GEval metrics."""

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import evaluate
from evals.utils.eval_llm_client import EvalLLMClient
import logging
from pathlib import Path
from deep_research.research import start_deep_research
import asyncio
from deep_research.utils.output_parser import (
    get_report,
    get_research_plan,
    get_sub_reports,
)
import os
from typing import List

logger = logging.getLogger(__name__)

evaluator_model = EvalLLMClient(model=os.getenv("JUDGE_EVALUATOR_MODEL"))

TEST_PROMPTS_DIR = Path(__file__).resolve().parents[0] / "eval_prompts"


def _write_test_report(report: str, session_id: str) -> str:
    """Write evaluation report under ``output/<session_id>/eval_report.md``."""
    session_dir = os.path.join("output", session_id)
    os.makedirs(session_dir, exist_ok=True)
    file_path = os.path.join(session_dir, "eval_report.md")
    with open(file_path, "w") as f:
        f.write(report)
    return file_path


def _get_test_cases() -> List[str]:
    """Load all test case files from ``evals/eval_prompts`` directory."""

    def _read_file(path: Path) -> str:
        if not path.is_file():
            raise FileNotFoundError(f"Expected file not found: {path}")
        return path.read_text(encoding="utf-8")

    sub_report_paths = sorted(path for path in TEST_PROMPTS_DIR.glob("*"))
    return [_read_file(path) for path in sub_report_paths]


async def run_evals() -> None:
    """Run deep research sessions for all eval prompts and trigger scoring."""
    test_cases = _get_test_cases()
    tasks = [asyncio.create_task(start_deep_research(msg=tc)) for tc in test_cases]
    session_ids = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Session ids to run evals: ", session_ids)
    for i, session_id in enumerate(session_ids):
        test_case = test_cases[i]
        run_deep_research_eval(session_id, test_case, evaluator_model)


def run_evals_for_test_case(session_id: str, test_case_filename: str) -> None:
    """Run eval for a specific test prompt file in ``eval_prompts``.

    Args:
        session_id: Session id whose outputs are evaluated.
        test_case_filename: Filename of the eval prompt (e.g., "test1.md").
                            If no extension is provided, ".md" is assumed.
    """
    # Resolve the path inside eval_prompts
    path = TEST_PROMPTS_DIR / test_case_filename
    # If no suffix provided, default to .md
    if path.suffix == "":
        path = path.with_suffix(".md")
    if not path.is_file():
        raise FileNotFoundError(f"Eval prompt file not found: {path}")

    test_case = path.read_text(encoding="utf-8")
    run_deep_research_eval(session_id, test_case, evaluator_model)


def run_deep_research_eval(
    session_id: str, test_case: str, evaluator: EvalLLMClient = evaluator_model
) -> None:
    """Run GEval metrics over the final report + sub-reports for a session."""
    correctness = GEval(
        name="Correctness & Faithfulness",
        criteria="Factual accuracy with no contradictions; every claim is supported by provided sources.",
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    coverage = GEval(
        name="Coverage & Depth",
        criteria="Answers every sub-question; surfaces key insights; explains tradeoffs/uncertainties.",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    reasoning = GEval(
        name="Reasoning Quality",
        criteria="Sound plan; appropriate tool use; avoids spurious steps; transparent logic.",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    evidence = GEval(
        name="Evidence Handling",
        criteria="High citation density; quotes faithful; links valid/resolve; citations support claims.",
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    presentation = GEval(
        name="Presentation",
        criteria="Clear structure, section headings, in-depth writing, meets the specific format and presentation asks of the user.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    synthesis = GEval(
        name="Synthesis",
        criteria="Sub-reports are integrated into a coherent final narrative; contradictions resolved; conclusions justified by sub-findings.",
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        threshold=0.7,
        model=evaluator,
        verbose_mode=False,
    )

    research_plan = get_research_plan(session_id)
    final_report = get_report(session_id)
    sub_reports = get_sub_reports(session_id)

    case = LLMTestCase(
        input=test_case,
        actual_output=final_report,
        context=[research_plan] + sub_reports,
    )

    metrics = [
        correctness,
        coverage,
        reasoning,
        evidence,
        presentation,
        synthesis,
    ]

    evaluation_result = evaluate(
        test_cases=[case],
        metrics=metrics,
    )

    for result in evaluation_result.test_results:
        evaluation_report = f"# Evaluation Report For {result.name}\n"
        for data in result.metrics_data:
            evaluation_report += f"- {data.name}[{'Success' if data.success else 'Fail'}]: {data.score}\n"
            evaluation_report += f"    - Reasoning: {data.reason}\n"
        _write_test_report(evaluation_report, session_id)
