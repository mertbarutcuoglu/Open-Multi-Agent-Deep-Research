"""
Tool definitions for the Deep Search Agent system.

This module contains the tool definitions following Anthropic's tool use format,
including detailed schemas and descriptions for optimal LLM performance.
"""

from typing import Dict, List, Any
from enum import Enum


class ToolName(str, Enum):
    WEB_SEARCH = "web_search"
    WEB_EXTRACT = "web_extract"
    RUN_SUBAGENT = "run_subagent"
    SAVE_RESEARCH_PLAN = "save_research_plan"
    COMPLETE_TASK = "complete_task"
    COMPLETE_SUB_TASK = "complete_sub_task"


TOOL_NAMES = [tool.value for tool in ToolName]

SAVE_RESEARCH_PLAN_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "save_research_plan",
        "description": "Save the research plan to a markdown file in a new session directory under output/.",
        "parameters": {
            "type": "object",
            "properties": {
                "research_plan": {
                    "type": "string",
                    "description": "The research plan content to save as markdown.",
                }
            },
            "required": ["research_plan"],
        },
    },
}

# Complete Task Tool Definition
COMPLETE_TASK_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": ToolName.COMPLETE_TASK.value,
        "description": (
            "Signal that the current research task is complete and provide a final"
            " report that should be returned to the user. Use this when you have"
            " finished the plan, gathered evidence, and produced a synthesis."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "final_report": {
                    "type": "string",
                    "description": (
                        "Concise final report or synthesis ready to deliver to the"
                        " user."
                    ),
                }
            },
            "required": ["final_report"],
            "additionalProperties": False,
        },
    },
}

COMPLETE_SUB_TASK_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": ToolName.COMPLETE_SUB_TASK.value,
        "description": (
            "Signal that the sub-task is complete and provide the consolidated sub"
            " report that should be handed off to the lead agent. Use this when the"
            " delegated research is done and you are ready to summarize findings."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sub_report": {
                    "type": "string",
                    "description": (
                        "Detailed sub-task report that captures findings, sources,"
                        " and recommendations for the lead agent."
                    ),
                }
            },
            "required": ["sub_report"],
            "additionalProperties": False,
        },
    },
}

# Create Sub Agent Tool Definition
# Run Blocking Sub-Agent Tool Definition
RUN_SUBAGENT_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_subagent",
        "description": (
            "Synchronously run a short-lived specialized sub-agent to complete a single, "
            "well-scoped subtask."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": (
                        "Prompt for the sub-agent. Provide concise, explicit "
                        "instructions on role, tone, constraints, and guardrails."
                    ),
                },
                "agent_id": {
                    "type": "string",
                    "description": (
                        "A unique and a meaningful id for an agent that briefly describes their task."
                        "It must be lower-cased written with snake case. Example: market_research_agent"
                    ),
                },
            },
            "required": ["prompt", "agent_id"],
            "additionalProperties": False,
        },
    },
}

# Tavily Search Tool Definition
TAVILY_SEARCH_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": """Search the web to find current information, facts, news, or any web-based content. This tool is ideal for finding recent information, research papers, news articles, company information, or general knowledge. The search returns ranked results with titles, URLs, content snippets, and optionally an AI-generated answer. Use this tool when you need to find information that may not be in your training data or when you need current/recent information. The tool supports both basic and advanced search depths - use advanced for more comprehensive results when researching complex topics.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string. Be specific and use relevant keywords. For example: 'latest AI research 2024', 'climate change effects on agriculture', 'Tesla stock price today'.",
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Search depth level. 'basic' provides quick results with generic content snippets (1 credit). 'advanced' provides more relevant and comprehensive results with better content snippets (2 credits). Use 'advanced' for complex research topics.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Maximum number of search results to return. Use 3-5 for quick searches, 10-15 for comprehensive research, up to 20 for exhaustive searches.",
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "Whether to include an AI-generated direct answer to the query. Set to true when you want a quick summary answer along with the search results.",
                },
                "include_raw_content": {
                    "type": "boolean",
                    "description": "Whether to include the full raw content from each result. Set to true when you need complete article content, false for just snippets.",
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific domains to include in search results (e.g., ['wikipedia.org', 'nature.com']). Use when you want results from specific authoritative sources.",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to exclude from search results (e.g., ['reddit.com', 'quora.com']). Use to filter out less reliable sources.",
                },
            },
            "required": ["query"],
        },
    },
}

# Tavily Extract Tool Definition
TAVILY_EXTRACT_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_extract",
        "description": """Extract and parse the complete content from specific web pages. This tool is perfect for reading full articles, research papers, documentation, or any web content when you have specific URLs. It returns the cleaned, parsed content in markdown or text format, removing ads, navigation, and other clutter. Use this tool when you need to read the complete content of known web pages, follow up on search results, or extract information from specific URLs. The tool can handle multiple URLs at once and provides high-quality content extraction.""",
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to extract content from. Each URL should be a complete, valid web address (e.g., 'https://example.com/article'). Can extract from multiple URLs in a single call.",
                },
                "include_images": {
                    "type": "boolean",
                    "description": "Whether to include images found on the pages in the extraction results. Set to true when images are important for understanding the content.",
                },
                "extract_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Extraction depth level. 'basic' provides standard content extraction (1 credit per 5 URLs). 'advanced' retrieves more comprehensive data including tables and embedded content with higher success rate (2 credits per 5 URLs).",
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "text"],
                    "description": "Output format for the extracted content. 'markdown' preserves formatting and structure. 'text' returns plain text (may increase latency).",
                },
            },
            "required": ["urls"],
        },
    },
}


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get all available tools for the research system.

    Returns:
        List of tool definitions that can be passed to the LLM API
    """
    return [
        TAVILY_SEARCH_TOOL,
        TAVILY_EXTRACT_TOOL,
        RUN_SUBAGENT_TOOL,
        SAVE_RESEARCH_PLAN_TOOL,
        COMPLETE_TASK_TOOL,
        COMPLETE_SUB_TASK_TOOL,
    ]


def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
    """
    Get a specific tool definition by name.

    Args:
        tool_name: Name of the tool to retrieve

    Returns:
        Tool definition dictionary

    Raises:
        ValueError: If tool name is not found
    """
    tools = {
        ToolName.WEB_SEARCH: TAVILY_SEARCH_TOOL,
        ToolName.WEB_EXTRACT: TAVILY_EXTRACT_TOOL,
        ToolName.RUN_SUBAGENT: RUN_SUBAGENT_TOOL,
        ToolName.SAVE_RESEARCH_PLAN: SAVE_RESEARCH_PLAN_TOOL,
        ToolName.COMPLETE_TASK: COMPLETE_TASK_TOOL,
        ToolName.COMPLETE_SUB_TASK: COMPLETE_SUB_TASK_TOOL,
    }

    if isinstance(tool_name, ToolName):
        key = tool_name
    else:
        try:
            key = ToolName(tool_name)
        except ValueError:
            available = [t.value for t in tools.keys()]
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available}"
            ) from None

    return tools[key]


def validate_tool_input(tool_name: str, tool_input: Dict[str, Any]) -> bool:
    """
    Validate tool input against the tool's schema.

    Args:
        tool_name: Name of the tool
        tool_input: Input parameters to validate

    Returns:
        True if input is valid

    Raises:
        ValueError: If validation fails
    """
    tool_def = get_tool_by_name(tool_name)
    schema = tool_def["function"]["parameters"]
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in tool_input:
            raise ValueError(f"Missing required field '{field}' for tool '{tool_name}'")

    # Basic type checking for known fields
    properties = schema.get("properties", {})
    for field, value in tool_input.items():
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get("type")

            if field_type == "string" and not isinstance(value, str):
                raise ValueError(f"Field '{field}' must be a string")
            elif field_type == "integer" and not isinstance(value, int):
                raise ValueError(f"Field '{field}' must be an integer")
            elif field_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"Field '{field}' must be a boolean")
            elif field_type == "array" and not isinstance(value, list):
                raise ValueError(f"Field '{field}' must be an array")

    return True
