"""
Prompt loading utilities

This module provides functionality to load and process prompt templates
from the prompts directory, including template variable replacement.
"""

import os
from datetime import datetime
from typing import Dict, Optional


class PromptLoadError(Exception):
    """Exception raised when prompt loading fails."""

    pass


def load_prompt(filename: str, variables: Optional[Dict[str, str]] = None) -> str:
    """
    Load a prompt from the prompts directory with template variable replacement.

    This function loads prompt files and replaces template variables with actual values.
    Currently supports {{.CurrentDate}} replacement and custom variables.

    Args:
        filename: Name of the prompt file to load (e.g., "research_lead_agent.md")
        variables: Optional dictionary of custom variables to replace in the prompt

    Returns:
        The loaded prompt content with variables replaced

    Raises:
        PromptLoadError: If the prompt file cannot be found or loaded

    Example:
        >>> prompt = load_prompt("research_lead_agent.md")
        >>> custom_prompt = load_prompt("custom.md", {"name": "John", "role": "researcher"})
    """
    prompt_path = os.path.join("deep_research", "prompts", filename)

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise PromptLoadError(f"Prompt file not found: {prompt_path}")
    except IOError as e:
        raise PromptLoadError(f"Error reading prompt file {prompt_path}: {e}")

    # Replace built-in template variables
    content = _replace_builtin_variables(content)

    # Replace custom variables if provided
    if variables:
        content = _replace_custom_variables(content, variables)

    return content


def _replace_builtin_variables(content: str) -> str:
    """
    Replace built-in template variables in the prompt content.

    Currently supports:
    - {{.CurrentDate}}: Replaced with current date in YYYY-MM-DD format

    Args:
        content: The prompt content to process

    Returns:
        Content with built-in variables replaced
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    content = content.replace("{{.CurrentDate}}", current_date)

    return content


def _replace_custom_variables(content: str, variables: Dict[str, str]) -> str:
    """
    Replace custom template variables in the prompt content.

    Variables should be in the format {{variable_name}} in the prompt.

    Args:
        content: The prompt content to process
        variables: Dictionary mapping variable names to their values

    Returns:
        Content with custom variables replaced
    """
    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        content = content.replace(placeholder, var_value)

    return content
