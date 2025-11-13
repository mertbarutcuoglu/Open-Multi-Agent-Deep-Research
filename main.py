"""CLI entrypoint for running research sessions and evals."""

import argparse
import asyncio
import contextlib
import logging

from dotenv import load_dotenv
from litellm.llms.custom_httpx.async_client_cleanup import (
    close_litellm_async_clients,
)

from deep_research.research import start_deep_research
from evals.deep_research import (
    run_evals,
    run_evals_for_test_case,
)

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def _cleanup_litellm_clients() -> None:
    """Close LiteLLM's cached async clients while the loop is still open."""
    with contextlib.suppress(Exception):
        await close_litellm_async_clients()


async def main() -> None:
    """Parse CLI arguments and dispatch to research or eval flows."""
    parser = argparse.ArgumentParser(description="A multi-agent deep research system.")

    parser.add_argument(
        "-q", "--query", type=str, help="Your query for starting a deep research."
    )
    parser.add_argument(
        "-e",
        "--evals",
        action="store_true",
        help="Runs evaluations for your test cases.",
    )
    parser.add_argument(
        "--run_eval",
        action="store_true",
        help="Run a specific test case for evaluation",
    )
    parser.add_argument(
        "-s", "--session_id", type=str, help="Session ID to run an evaluation"
    )
    parser.add_argument(
        "-t",
        "--test_case",
        type=str,
        help=(
            "Eval prompt filename under evals/eval_prompts (e.g., test1.md). "
            "If extension omitted, .md is assumed."
        ),
    )

    args = parser.parse_args()

    try:
        if args.query:
            await start_deep_research(args.query)
        elif args.evals:
            await run_evals()
        elif args.run_eval:
            if not args.session_id or not args.test_case:
                parser.error("--run_eval requires both --session_id and --test_case.")
            run_evals_for_test_case(args.session_id, args.test_case)
        else:
            parser.print_help()
    finally:
        await _cleanup_litellm_clients()


if __name__ == "__main__":
    asyncio.run(main())
