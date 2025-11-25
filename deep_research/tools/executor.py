"""
Tool executor for the Deep Search Agent system.

This module handles the execution of tools, providing a unified interface
for tool calling and result formatting.
"""

from typing import Dict, Any, Optional, Sequence

from deep_research.tools.definitions import validate_tool_input, TOOL_NAMES
from deep_research.services.search_service import SearchService, SearchError
from deep_research.services.llm_service import LLMService
from deep_research.tools.definitions import ToolName
from deep_research.utils.session_id import get_session_id

import os
import uuid
import json


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""

    pass


class ToolExecutor:
    """
    Handles execution of tools for the research system.

    This class provides a unified interface for executing different types of tools,
    handling parameter validation, execution, and result formatting.
    """

    def __init__(
        self,
        available_tools: Optional[Sequence[ToolName | str]] = None,
    ) -> None:
        """
        Initialize the tool executor.

        Args:
            available_tools: List of available tools for this executor instance.
            tavily_api_key: Tavily API key (if None, will use env var)
        """
        raw_tools = available_tools if available_tools is not None else TOOL_NAMES
        self.available_tools = [
            tool.value if isinstance(tool, ToolName) else tool for tool in raw_tools
        ]

        try:
            self.tavily_client = SearchService()
        except SearchError as e:
            raise ToolExecutionError(f"Failed to initialize Tavily client: {e}")

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool with the given input.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            context: Optional metadata describing the caller (agent, step, etc.)

        Returns:
            Dictionary containing the tool execution result

        Raises:
            ToolExecutionError: If tool execution fails
        """
        try:
            return await self._execute_tool_inner(
                tool_name,
                tool_input,
                context=context,
            )
        except Exception as e:
            if isinstance(e, ToolExecutionError):
                raise
            raise ToolExecutionError(f"Tool execution failed for {tool_name}: {e}")

    async def _execute_tool_inner(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if tool_name not in self.available_tools:
            raise ToolExecutionError(
                f"Tool '{tool_name}' is not allowed for this executor instance."
            )

        validate_tool_input(tool_name, tool_input)

        if tool_name == "web_search":
            return await self._execute_tavily_search(tool_input)
        if tool_name == "web_extract":
            return await self._execute_tavily_extract(tool_input)
        if tool_name == "run_subagent":
            return await self._execute_run_subagent(
                tool_input,
                context=context,
            )
        if tool_name == "save_research_plan":
            return self._execute_save_research_plan(tool_input)
        if tool_name == "complete_task":
            return self._execute_complete_task(tool_input, context=context)
        if tool_name == "complete_sub_task":
            return self._execute_complete_sub_task(tool_input, context=context)

        raise ToolExecutionError(f"Unknown tool: {tool_name}")

    def _execute_save_research_plan(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        research_plan = tool_input["research_plan"]
        file_path = self._write_to_file(research_plan, "research_plan.md")
        message = f"Research plan saved to {file_path}"
        return {
            "success": True,
            "tool_name": "save_research_plan",
            "file_path": file_path,
            "message": message,
            "formatted_content": message,
        }

    def _write_to_file(self, content: str, file_name: str) -> str:
        session_dir = os.path.join("output", get_session_id())
        os.makedirs(session_dir, exist_ok=True)
        file_path = os.path.join(session_dir, file_name)
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def _normalize_filename_component(self, value: Optional[str], default: str) -> str:
        if not value:
            return default
        sanitized = "".join(
            ch
            if ("a" <= ch <= "z")
            or ("A" <= ch <= "Z")
            or ("0" <= ch <= "9")
            or ch in {"-", "_"}
            else "-"
            for ch in str(value)
        ).strip("-_")
        return sanitized or default

    async def _execute_run_subagent(
        self,
        tool_input: Dict[str, str],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from deep_research.agents.agent import Agent

        prompt = tool_input["prompt"]
        agent_id = tool_input.get("agent_id") or f"sub-agent-{uuid.uuid4().hex[:6]}"
        llm_client = LLMService(model=os.getenv("SUB_AGENT_MODEL"))
        agent = Agent(
            agent_id=agent_id,
            prompt_path="research_sub_agent.md",
            llm_client=llm_client,
            initial_user_message=prompt,
            tools=[
                ToolName.WEB_EXTRACT,
                ToolName.WEB_SEARCH,
                ToolName.COMPLETE_SUB_TASK,
            ],
            parent_agent_id=context.get("agent_id") if context else None,
        )
        agent_response, _ = await agent.run()

        # Extract human-readable content for the parent agent while keeping the raw payload
        formatted_content = ""
        if isinstance(agent_response, dict):
            choices = agent_response.get("choices") or []
            if choices:
                formatted_content = choices[0].get("message", {}).get("content") or ""
            if not formatted_content:
                formatted_content = json.dumps(agent_response, ensure_ascii=False)
        else:
            formatted_content = str(agent_response)

        return {
            "success": True,
            "tool_name": "run_subagent",
            "formatted_content": formatted_content,
            "raw_response": agent_response,
            "spawned_agent_id": agent_id,
        }

    def _execute_complete_task(
        self,
        tool_input: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        final_report = tool_input["final_report"]
        self._write_to_file(final_report, "report.md")
        return {
            "success": True,
            "tool_name": "complete_task",
            "final_report": final_report,
            "formatted_content": final_report,
            "task_completed": True,
        }

    def _execute_complete_sub_task(
        self,
        tool_input: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sub_report = tool_input["sub_report"]
        agent_id = (context or {}).get("agent_id")
        tool_call_id = (context or {}).get("tool_call_id")
        step_index = (context or {}).get("step_index")

        agent_component = self._normalize_filename_component(
            agent_id,
            default="sub_agent",
        )
        call_component = self._normalize_filename_component(
            tool_call_id,
            default="complete",
        )
        step_suffix = f"_step{step_index}" if isinstance(step_index, int) else ""
        file_name = f"sub_report_{agent_component}_{call_component}{step_suffix}.md"
        file_path = self._write_to_file(sub_report, file_name)

        return {
            "success": True,
            "tool_name": "complete_sub_task",
            "sub_report": sub_report,
            "formatted_content": sub_report,
            "file_path": file_path,
            "task_completed": True,
            "agent_id": agent_id,
        }

    async def _execute_tavily_search(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Tavily search tool.

        Args:
            tool_input: Search parameters

        Returns:
            Dictionary containing search results and formatted content
        """
        try:
            # Extract parameters with defaults
            query = tool_input["query"]
            search_depth = tool_input.get("search_depth", "basic")
            max_results = tool_input.get("max_results", 5)
            include_answer = tool_input.get("include_answer", False)
            include_raw_content = tool_input.get("include_raw_content", False)
            include_domains = tool_input.get("include_domains")
            exclude_domains = tool_input.get("exclude_domains")

            # Perform the search without blocking the event loop
            raw_results = await self.tavily_client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )

            # Format results for agent consumption
            formatted_content = self.tavily_client.format_search_results(raw_results)

            return {
                "success": True,
                "tool_name": "web_search",
                "query": query,
                "formatted_content": formatted_content,
                "raw_results": raw_results,
                "result_count": len(raw_results.get("results", [])),
                "has_answer": bool(raw_results.get("answer")),
            }

        except SearchError as e:
            raise ToolExecutionError(f"Tavily search failed: {e}")

    async def _execute_tavily_extract(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Tavily extract tool.

        Args:
            tool_input: Extract parameters

        Returns:
            Dictionary containing extraction results and formatted content
        """
        try:
            # Extract parameters with defaults
            urls = tool_input["urls"]
            include_images = tool_input.get("include_images", False)
            extract_depth = tool_input.get("extract_depth", "basic")
            format_type = tool_input.get("format", "markdown")

            # Perform the extraction without blocking the event loop
            raw_results = await self.tavily_client.extract(
                urls=urls,
                include_images=include_images,
                extract_depth=extract_depth,
                format=format_type,
            )

            # Format results for agent consumption
            formatted_content = self.tavily_client.format_extract_results(raw_results)

            return {
                "success": True,
                "tool_name": "web_extract",
                "urls": urls,
                "formatted_content": formatted_content,
                "raw_results": raw_results,
                "successful_extractions": len(raw_results.get("results", [])),
                "failed_extractions": len(raw_results.get("failed_results", [])),
            }

        except SearchError as e:
            raise ToolExecutionError(f"Tavily extract failed: {e}")

    def get_executor_info(self) -> Dict[str, Any]:
        """
        Get information about the tool executor.

        Returns:
            Dictionary with executor information
        """
        return {
            "allowed_tools": self.available_tools,
            "tavily_client_info": self.tavily_client.get_client_info(),
        }


# Global executor instance for convenience
_global_executor: Optional[ToolExecutor] = None


def get_tool_executor(
    tavily_api_key: Optional[str] = None,
) -> ToolExecutor:
    """
    Get a tool executor instance (singleton pattern).

    Args:
        tavily_api_key: Tavily API key (only used for first initialization)

    Returns:
        ToolExecutor instance
    """
    global _global_executor

    if _global_executor is None:
        _global_executor = ToolExecutor(
            tavily_api_key=tavily_api_key,
        )

    return _global_executor


def execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to execute a tool using the global executor.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool

    Returns:
        Dictionary containing the tool execution result

    Raises:
        ToolExecutionError: If tool execution fails
    """
    executor = get_tool_executor()
    return executor.execute_tool(tool_name, tool_input, context=context)


def format_tool_result_for_llm(result: Dict[str, Any]) -> str:
    """
    Format tool execution result for LLM consumption.

    This function takes the result from execute_tool and formats it
    as a string suitable for returning to the LLM as a tool_result.

    Args:
        result: Result dictionary from execute_tool

    Returns:
        Formatted string for LLM tool_result content
    """
    if not result.get("success", False):
        return f"Tool execution failed: {result.get('error', 'Unknown error')}"

    tool_name = result.get("tool_name", "unknown")
    formatted_content = result.get("formatted_content", "")

    if tool_name == "web_search":
        query = result.get("query", "")
        result_count = result.get("result_count", 0)
        has_answer = result.get("has_answer", False)

        header = f"Search Results for: '{query}' ({result_count} results"
        if has_answer:
            header += ", includes AI answer"
        header += ")\n\n"

        return header + formatted_content

    elif tool_name == "web_extract":
        urls = result.get("urls", [])
        successful = result.get("successful_extractions", 0)
        failed = result.get("failed_extractions", 0)

        header = f"Content Extraction from {len(urls)} URL(s) "
        header += f"({successful} successful, {failed} failed)\n\n"

        return header + formatted_content

    else:
        return formatted_content
