"""
LLM service for the Deep Search Agent system.

This module provides a service class for interacting with LLMs via LiteLLM,
supporting Anthropic, Azure OpenAI, OpenAI, and other providers.
Handles authentication, rate limiting, and error management.
"""

import asyncio
import os
import time
from typing import Dict, List, Optional

from litellm import acompletion


class LLMError(Exception):
    """Exception raised when LLM service operations fail."""

    pass


class LLMService:
    """
    Service for interacting with LLMs via LiteLLM.

    This class handles all interactions with supported LLM providers through the LiteLLM SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openrouter/x-ai/grok-4-fast",
        max_tokens: int = 64000,
        rate_limit_delay: float = 0.5,
    ) -> None:
        """
        Initialize the LLM service.

        Args:
            api_key: API key for the LLM provider (if None, will use ANTHROPIC_API_KEY, AZURE_API_KEY,
                                                   or OPENAI_API_KEY env var)
            model: Default model to use for requests
            max_tokens: Default maximum tokens for responses
            rate_limit_delay: Delay between requests to avoid rate limiting
        """
        # LiteLLM uses environment variables for API keys (ANTHROPIC_API_KEY, AZURE_API_KEY, OPENAI_API_KEY, etc.)
        self.api_key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("AZURE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise LLMError(
                "No API key provided. Set OPENROUTER_API_KEY, ANTHROPIC_API_KEY, AZURE_API_KEY, or OPENAI_API_KEY in your environment."
            )
        self.model = model
        self.max_tokens = max_tokens
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self._rate_limit_lock: Optional[asyncio.Lock] = None
        self._last_response: Optional[Dict] = None

    async def _apply_rate_limiting(self) -> None:
        """Apply rate limiting by waiting without blocking the event loop."""
        if self.rate_limit_delay <= 0:
            self.last_request_time = time.time()
            return

        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)

            self.last_request_time = time.time()

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
    ) -> str:
        """
        Generate a response from the configured LLM.

        Args:
            messages: Conversation messages in OpenAI-compatible format.
            tools: Optional tool definitions for tool use.
            tool_choice: Optional tool choice directive passed to the API.

        Returns:
            The assistant message content as plain text.

        Raises:
            LLMError: If the API call fails
        """
        # Apply rate limiting without blocking the loop
        await self._apply_rate_limiting()

        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 1,
            "messages": messages,
        }
        if tools:
            api_params["tools"] = tools
        if tool_choice:
            api_params["tool_choice"] = tool_choice

        try:
            response = await acompletion(**api_params)
            self._last_response = response
        except Exception as e:
            raise LLMError(f"Unexpected error calling LLM: {e}")

        # Extract text content from response (OpenAI format)
        choices = (response or {}).get("choices") or []
        if choices and choices[0].get("message", {}).get("content"):
            content = choices[0]["message"]["content"]
            return content

        raise LLMError("Empty response from API")

    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        *,
        tool_choice: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a response from the LLM with tool support, returning full response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Tool definitions
            tool_choice: Optional tool choice configuration passed to the API

        Returns:
            Full response object from the API (OpenAI/LiteLLM format)

        Raises:
            LLMError: If the API call fails
        """
        # Apply rate limiting without blocking the loop
        await self._apply_rate_limiting()

        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 1,
            "messages": messages,
            "tools": tools,
        }
        if tool_choice is not None:
            api_params["tool_choice"] = tool_choice

        try:
            response = await acompletion(**api_params)
            self._last_response = response
            return response
        except Exception as e:
            raise LLMError(f"Unexpected error calling LLM: {e}")
