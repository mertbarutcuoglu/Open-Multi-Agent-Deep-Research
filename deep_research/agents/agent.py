"""Base agent class"""

from deep_research.services.llm_service import LLMService
from deep_research.tools.executor import ToolExecutor, format_tool_result_for_llm
from deep_research.tools.definitions import (
    get_available_tools,
    get_tool_by_name,
    ToolName,
    TOOL_NAMES,
)
from deep_research.utils.memory import Memory
from deep_research.utils.prompt_loader import load_prompt
from deep_research.utils.session_id import get_session_id
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Sequence


INTERLEAVED_THINKING_PROMPT = (
    "Reflect on the latest tool results before selecting your next action. Summarize the new "
    "information, how it affects your plan, and outline the most sensible next step. Do not call "
    "any tools in this response; respond with reasoning only."
)


tracer = trace.get_tracer(__name__)


class Agent:
    """
    LLM Agent with persistent memory and tool access.

    This agent owns three responsibilities:
      1) State: load the system prompt, persist the evolving conversation,
         and record tool I/O via `Memory`.
      2) Control: call the LLM, decide when to invoke tools, execute them,
         and feed results back into the model.
      3) Completion: detect when a task is finished or when the step budget
         is exhausted and nudge the model to synthesize results.
    """

    def __init__(
        self,
        agent_id: str,
        prompt_path: str,
        llm_client: LLMService,
        parent_agent_id: Optional[str] = None,
        initial_user_message: str = "",
        max_steps: int = 25,
        tools: Optional[Sequence[ToolName | str]] = None,
        max_consecutive_no_tool: int = 2,
        enable_interleaved_thinking: bool = False,
        enable_memory_autosave: bool = True,
        autosave_every: int = 1,
    ) -> None:
        """Configure agent with id, prompt, LLM, and tool policy."""
        self.agent_id = agent_id
        self.llm_client = llm_client
        self.max_steps = max_steps
        self.max_consecutive_no_tool = max_consecutive_no_tool
        self.parent_agent_id = parent_agent_id
        self.enable_interleaved_thinking = enable_interleaved_thinking
        self.memory = Memory(
            agent_id,
            llm_client,
            autosave=enable_memory_autosave,
            autosave_every=autosave_every,
        )
        self._prompt_path = prompt_path
        self._initial_user_message = initial_user_message
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        if tools is None:
            self.tools = get_available_tools()
            allowed_tool_names = list(TOOL_NAMES)
        else:
            allowed_tool_names: List[str] = []
            tool_definitions: List[Dict[str, Any]] = []
            for tool in tools:
                tool_name = tool.value if isinstance(tool, ToolName) else tool
                tool_definitions.append(get_tool_by_name(tool_name))
                allowed_tool_names.append(tool_name)
            self.tools = tool_definitions

        self.tool_executor = ToolExecutor(
            allowed_tool_names,
        )

    async def _start_memory(
        self, prompt_path: str, initial_user_message: Optional[str]
    ) -> None:
        """Seed memory with the system prompt and optional initial user message."""
        system_prompt = load_prompt(prompt_path)
        await self.memory.add_system_message(system_prompt)
        if initial_user_message:
            await self.add_user_message(initial_user_message)

    async def add_user_message(self, content: str) -> None:
        """Add a user message to the agent memory."""
        await self.memory.add_user_message(content)

    async def _run_interleaved_thinking_step(
        self, *, session_id: Optional[str] = None
    ) -> None:
        """Ask the model to reflect without tool calls, then store reflection."""
        current_session_id = session_id or get_session_id()
        with tracer.start_as_current_span(
            "agent.interleaved_thinking",
            attributes={
                "agent_id": self.agent_id,
                "parent_agent_id": self.parent_agent_id or "",
                "session_id": current_session_id,
                "thought_type": "reflection",
            },
        ) as thinking_span:
            thinking_span.add_event(
                "interleaved.prompt.sent",
                attributes={"thought_type": "reflection"},
            )

        model_messages = await self.memory.get_model_messages()
        reflection_messages = model_messages + [
            {
                "role": "assistant",
                "content": INTERLEAVED_THINKING_PROMPT,
            }
        ]

        try:
            self._log("Invoking LLM for interleaved reflection")
            reflection_content = await self.llm_client.generate_response(
                reflection_messages
            )
            self._log("Interleaved reflection response received")
        except Exception as exc:
            self._log(
                f"Interleaved thinking failed: {exc}",
                level=logging.ERROR,
                exc_info=exc,
            )
            thinking_span.record_exception(exc)
            thinking_span.set_status(Status(StatusCode.ERROR))
            return

        reflection_content = (reflection_content or "").strip()
        self._log(f"Reflection content: {reflection_content}", level=logging.INFO)
        thinking_span.add_event(
            "interleaved.response.received",
            attributes={"has_content": bool(reflection_content)},
        )
        if not reflection_content:
            self._log("Interleaved reflection returned empty content")
            return

        await self.memory.add_assistant_message(f"[Reflection]\n{reflection_content}")

    async def run(self) -> tuple[Dict[str, Any], str]:
        """Run the agent loop and return (last_raw_response, session_id)."""
        session_id = get_session_id()
        with tracer.start_as_current_span(
            "agent.run",
            attributes={
                "agent_id": self.agent_id,
                "parent_agent_id": self.parent_agent_id or "",
                "session_id": session_id,
                "step_index": -1,
                "max_steps": self.max_steps,
            },
        ):
            await self._start_memory(self._prompt_path, self._initial_user_message)
            return await self._run_internal(session_id=session_id), session_id

    async def _run_internal(self, *, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Main loop: get LLM response, execute tools, and persist results."""
        loop_session_id = session_id or get_session_id()
        last_response: Dict[str, Any] = {}
        task_completed = False
        completion_prompt_added = False

        with tracer.start_as_current_span(
            "agent.run_loop",
            attributes={
                "agent_id": self.agent_id,
                "parent_agent_id": self.parent_agent_id or "",
                "session_id": loop_session_id,
                "max_steps": self.max_steps,
                "step_index": -1,
            },
        ):
            for step_index in range(self.max_steps):
                with tracer.start_as_current_span(
                    "agent.step",
                    attributes={
                        "agent_id": self.agent_id,
                        "parent_agent_id": self.parent_agent_id or "",
                        "session_id": loop_session_id,
                        "step_index": step_index,
                        "max_steps": self.max_steps,
                    },
                ) as step_span:
                    self._log(f"--- Step {step_index} start ---")
                    if (
                        not task_completed
                        and not completion_prompt_added
                        and step_index == self.max_steps - 1
                    ):
                        completion_prompt = self._build_max_step_completion_prompt()
                        if completion_prompt:
                            with tracer.start_as_current_span(
                                "agent.completion_prompt",
                                attributes={
                                    "agent_id": self.agent_id,
                                    "parent_agent_id": self.parent_agent_id or "",
                                    "session_id": loop_session_id,
                                    "step_index": step_index,
                                    "max_steps": self.max_steps,
                                    "completion_hint": True,
                                },
                            ):
                                step_span.add_event(
                                    "completion.prompt_added",
                                    attributes={
                                        "completion_hint": True,
                                        "step_index": step_index,
                                        "max_steps": self.max_steps,
                                    },
                                )
                                await self.add_user_message(completion_prompt)
                                completion_prompt_added = True

                    response = await self.llm_client.generate_response_with_tools(
                        await self.memory.get_model_messages(), tools=self.tools
                    )
                    self._log("LLM response received")
                    last_response = response

                    assistant_message = (response.get("choices") or [{}])[0].get(
                        "message", {}
                    ) or {}
                    assistant_content = assistant_message.get("content") or ""
                    tool_calls = assistant_message.get("tool_calls") or []
                    self._log(
                        "Assistant content length: " + str(len(assistant_content or ""))
                    )
                    self._log("Assistant content: " + str(assistant_content))
                    if tool_calls:
                        await self.memory.add_assistant_message_with_tool_calls(
                            tool_calls, assistant_content
                        )

                    if tool_calls:
                        self._log("Processing tool calls")
                        tool_call_ids = []
                        tool_call_names = []
                        tool_execution_coros = []

                        for tc in tool_calls:
                            tool_name = tc["function"]["name"]
                            tool_call_id = tc.get("id")

                            raw_args = tc["function"].get("arguments") or "{}"
                            try:
                                args = json.loads(raw_args)
                            except json.JSONDecodeError:
                                args = {}

                            self._log(
                                f"Scheduling tool '{tool_name}' with args: {args}"
                            )
                            step_span.add_event(
                                "tool.scheduled",
                                attributes={
                                    "tool_call_id": tool_call_id,
                                    "tool_name": tool_name,
                                    "step_index": step_index,
                                    "session_id": loop_session_id,
                                },
                            )

                            tool_call_ids.append(tool_call_id)
                            tool_call_names.append(tool_name)
                            tool_execution_coros.append(
                                self.tool_executor.execute_tool(
                                    tool_name,
                                    args,
                                    context={
                                        "agent_id": self.agent_id,
                                        "tool_call_id": tool_call_id,
                                        "step_index": step_index,
                                    },
                                )
                            )

                        self._log("Awaiting tool execution results")
                        step_span.add_event(
                            "tool.execution.batch_started",
                            attributes={"count": len(tool_execution_coros)},
                        )
                        tool_results = await asyncio.gather(
                            *tool_execution_coros, return_exceptions=True
                        )
                        self._log("Tool executions completed")
                        step_span.add_event(
                            "tool.execution.batch_completed",
                            attributes={"count": len(tool_execution_coros)},
                        )

                        for tool_call_id, tool_name, result in zip(
                            tool_call_ids, tool_call_names, tool_results
                        ):
                            if isinstance(result, Exception):
                                error_message = (
                                    f"Tool '{tool_name}' execution failed: {result}"
                                )
                                self._log(
                                    error_message,
                                    level=logging.ERROR,
                                    exc_info=result,
                                )
                                step_span.record_exception(result)
                                formatted_result = {
                                    "success": False,
                                    "tool_name": tool_name,
                                    "error": error_message,
                                }
                            else:
                                self._log(f"Tool '{tool_name}' succeeded")
                                formatted_result = result
                                if formatted_result.get("task_completed"):
                                    task_completed = True
                            step_span.add_event(
                                "tool.result",
                                attributes={
                                    "tool_call_id": tool_call_id,
                                    "tool_name": tool_name,
                                    "status": "error"
                                    if isinstance(result, Exception)
                                    else "success",
                                    "task_completed": bool(
                                        formatted_result.get("task_completed")
                                    ),
                                    "session_id": loop_session_id,
                                },
                            )
                            await self.memory.add_tool_message(
                                format_tool_result_for_llm(formatted_result),
                                tool_call_id,
                            )

                        # Do not run interleaved thinking for report saving related tools
                        if (
                            self.enable_interleaved_thinking
                            and not (
                                tool_name == ToolName.SAVE_RESEARCH_PLAN
                                or tool_name == ToolName.COMPLETE_TASK
                                or tool_name == ToolName.COMPLETE_SUB_TASK
                            )
                            and not task_completed
                            and step_index % 3 == 0
                        ):
                            self._log("Running interleaved thinking after tools")
                            await self._run_interleaved_thinking_step(
                                session_id=loop_session_id
                            )

                        if task_completed:
                            self._log("Task completed; exiting loop")
                            step_span.set_attribute("task_completed", True)
                            await self.memory.save()
                            break
                    else:
                        await self.memory.add_assistant_message(assistant_content)

                    if task_completed:
                        break

        last_response = last_response or {"choices": []}
        return last_response

    def _build_max_step_completion_prompt(self) -> Optional[str]:
        """Return a completion hint message when max_steps is reached."""
        tool_name = self._get_completion_tool_name()
        if not tool_name:
            return None

        if tool_name == "complete_sub_task":
            return (
                "You have reached the maximum number of steps. Synthesize your findings,"
                " then call the `complete_sub_task` tool with your sub-report to wrap up."
            )

        return (
            "You have reached the maximum number of steps. Synthesize your findings,"
            " then call the `complete_task` tool with your final report to finish."
        )

    def _get_completion_tool_name(self) -> Optional[str]:
        """Pick the appropriate completion tool if available."""
        available = getattr(self.tool_executor, "available_tools", [])
        if "complete_task" in available:
            return "complete_task"
        if "complete_sub_task" in available:
            return "complete_sub_task"
        return None

    def _log(
        self,
        msg: str,
        *,
        level: int = logging.INFO,
        exc_info: Optional[BaseException] = None,
    ) -> None:
        """Lightweight info logger."""
        session_id = get_session_id()
        exc_info_value = (
            (exc_info.__class__, exc_info, exc_info.__traceback__) if exc_info else None
        )
        self._logger.log(
            level,
            "[agent=%s session=%s] %s",
            self.agent_id,
            session_id,
            msg,
            exc_info=exc_info_value,
        )
