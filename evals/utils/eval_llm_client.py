"""Wrapper to adapt LiteLLM to DeepEval's model interface."""

import logging

from litellm import acompletion, completion
from deepeval.models.base_model import DeepEvalBaseLLM
from pydantic import BaseModel
import instructor


logger = logging.getLogger(__name__)


class EvalLLMClient(DeepEvalBaseLLM):
    """Minimal DeepEvalBaseLLM implementation using LiteLLM chat completions."""

    def __init__(
        self,
        model: str,
    ) -> None:
        """Initialize with a model id resolvable by LiteLLM."""
        self.model = model
        self.client = instructor.from_litellm(completion)

    def load_model(self) -> str:
        """Return the configured model name for DeepEval bookkeeping."""
        return self.model

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """Synchronously generate a structured response matching ``schema``."""
        messages = [{"content": prompt, "role": "user"}]
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, response_model=schema
            )
        except Exception as e:
            logger.exception("EvalLLMClient.generate failed: %s", e)
            response = schema.model_construct()

        return response

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """Asynchronously generate a structured response matching ``schema``."""
        client = instructor.from_litellm(acompletion)

        messages = [{"content": prompt, "role": "user"}]
        try:
            response = await client.chat.completions.create(
                model=self.model, messages=messages, response_model=schema
            )

        except Exception as e:
            logger.exception("EvalLLMClient.a_generate failed: %s", e)
            response = schema.model_construct()

        return response

    def get_model_name(self) -> str:
        """Return a user-friendly model label for reports."""
        return f"LiteLLM Model({self.model})"
