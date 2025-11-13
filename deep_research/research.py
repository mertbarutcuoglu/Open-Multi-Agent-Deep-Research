"""Top-level orchestration for deep research and citation pass."""

from deep_research.services.llm_service import LLMService
from deep_research.tools.definitions import ToolName
from deep_research.agents.agent import Agent
from deep_research.utils.citation_context import (
    build_citation_agent_message,
    load_citation_context,
)
import os


async def start_deep_research(msg: str) -> str:
    """Run lead researcher then citation editor; return session id."""
    lead_agent_llm_client = LLMService(model=os.getenv("LEAD_AGENT_MODEL"))
    lead_researcher_agent = Agent(
        agent_id="lead_researcher",
        prompt_path="research_lead_agent.md",
        llm_client=lead_agent_llm_client,
        tools=[
            ToolName.RUN_SUBAGENT,
            ToolName.SAVE_RESEARCH_PLAN,
            ToolName.COMPLETE_TASK,
        ],
        initial_user_message=msg,
        max_steps=50,
    )
    _, session_id = await lead_researcher_agent.run()
    try:
        citation_context = load_citation_context(session_id)
    except FileNotFoundError:
        return session_id

    citation_agent_llm_client = LLMService(model=os.getenv("CITATION_EXTRACTOR_MODEL"))
    citation_message = build_citation_agent_message(citation_context)
    citation_agent = Agent(
        agent_id="citation_editor",
        prompt_path="citation_agent.md",
        llm_client=citation_agent_llm_client,
        tools=[ToolName.COMPLETE_TASK],
        initial_user_message=citation_message,
        max_steps=10,
        enable_interleaved_thinking=False,
    )
    await citation_agent.run()
    return session_id
