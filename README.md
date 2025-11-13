# Open Multi-Agent Deep Research
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE-MIT.md)

An opinionated, model-agnostic deep research system that orchestrates multiple agents to plan, search, extract, and synthesize high‑quality answers. It runs on top of LiteLLM, uses Tavily for web search/extract, writes all artifacts to sessioned folders, and includes automatic citation pass and G-Evals-based scoring.

## Features
- Model-agnostic via LiteLLM (OpenRouter, OpenAI, Anthropic, Azure, etc.)
- Multi-agent orchestration: lead planner, on-demand sub‑agents, citation editor
- Web tools: `web_search` and `web_extract` powered by Tavily
- Simple memory with automatic summarization of older turns
- Optional interleaved “reflect then act” thinking
- Deterministic output folders per session (`output/<session_id>`)
- Built‑in evaluation with DeepEval GEval metrics

## Getting Started
- Pre-reqs
  - Python 3.10+
  - API keys: `TAVILY_API_KEY` plus one provider key supported by LiteLLM (e.g., `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `AZURE_API_KEY`).
- Install Dependencies
  - This project uses uv for Python package management.
  - Install dependencies with: `uv pip install -r pyproject.toml`
  - This will install all dependencies specified in `pyproject.toml`.
- Configure
  - Create a `.env` based on `.env.example` and set:
    - `LEAD_AGENT_MODEL` and `SUB_AGENT_MODEL` (model IDs supported by your chosen provider). Optionally, if you are going to run evals, set `JUDGE_EVALUATOR_MODEL`.
    - `TAVILY_API_KEY` and a provider API key (e.g., `OPENROUTER_API_KEY`)
  - Provider preference order in code is: `OPENROUTER_API_KEY` → `ANTHROPIC_API_KEY` → `AZURE_API_KEY` → `OPENAI_API_KEY`.
- Important limitation
  - Both `LEAD_AGENT_MODEL`, `SUB_AGENT_MODEL` and `JUDGE_EVALUATOR_MODEL` must come from the same provider you’ve authenticated with (since one provider key is selected at runtime).

## Usage
- CLI
  - Run a research session: `uv run python main.py -q "Your question to research"`
  - Run all evals: `uv run python main.py --evals`
  - Run a specific eval on an existing session: `uv run python main.py --run_eval -s <session_id> -t <eval_filename>` (e.g., `-t test1.md`)
- Programmatic
  - Start research and get the session id:
    ```python
    import asyncio
    from deep_research.research import start_deep_research

    async def run():
        session_id = await start_deep_research("What are the benefits of intermittent fasting?")
        print("Session:", session_id)

    asyncio.run(run())
    ```
  - Read outputs later:
    ```python
    from deep_research.utils.output_parser import get_report, get_research_plan, get_sub_reports

    plan = get_research_plan(session_id)
    report = get_report(session_id)
    subs = get_sub_reports(session_id)
    ```
- Outputs
  - Everything lands in `output/<session_id>`:
    - `research_plan.md` (lead agent’s plan)
    - `sub_report_*.md` (per-subtask deliverables)
    - `report.md` (final synthesized report; later citation-edited)
    - `agent_id/memory.json` (full message+tool audit trail per agent)

## Developer Commands
- Lint
  - Check: `uv run ruff check .`
  - Auto-fix: `uv run ruff check --fix .`
- Tests
  - Run all: `uv run pytest -q`
- Evals
  - All cases: `uv run python main.py --evals`
  - Single case: `uv run python main.py --run_eval -s <session_id> -t <eval_filename>` (e.g., `-t test1.md`)

## Examples
You can find an example deep research output for the eval cases defined under `evals/eval_prompts/test1.md` in `example_outputs/autonomous_vehicles_safety_report`. This example is created using models defined in `.env.example` and evaluated using the judge model also defined in `.env.example`.

## Project Structure
```
/
├── deep_research/                 # Core research package
│   ├── agents/
│   │   └── agent.py             # Agent loop, tool calling, memory integration
│   ├── services/
│   │   ├── llm_service.py       # LiteLLM wrapper (provider-agnostic)
│   │   └── search_service.py    # Tavily wrapper (search/extract + formatting)
│   ├── tools/
│   │   ├── definitions.py       # Tool schemas and validation
│   │   └── executor.py          # Executes tools, spawns sub-agents, writes artifacts
│   ├── prompts/
│   │   ├── research_lead_agent.md
│   │   ├── research_sub_agent.md
│   │   └── citation_agent.md
│   ├── utils/
│   │   ├── memory.py            # Turn-bounded memory with summarization and audit trail
│   │   ├── output_parser.py     # Load plan/report/sub-reports from output/
│   │   ├── citation_context.py  # Prepare context for citation editor
│   │   ├── prompt_loader.py     # Template/date substitution for prompts
│   │   └── session_id.py        # Stable per-run session id
│   └── research.py              # Orchestrates lead + citation agents
├── evals/                       # GEval metrics and prompts
│   ├── deep_research.py
│   ├── eval_prompts/
│   └── utils/
├── tests/                       # Unit tests
│   ├── test_output_parser.py
│   ├── test_citation_context.py
│   └── test_memory_integration.py
├── main.py                      # CLI entrypoint
├── output/                      # Session artifacts (generated at runtime)
├── pyproject.toml
├── .env.example                 # Template env config
├── README.md
└── LICENSE-MIT.md
```

## License
This project is licensed under the MIT License. See `LICENSE-MIT.md`.
