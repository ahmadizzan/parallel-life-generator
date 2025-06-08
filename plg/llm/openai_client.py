from typing import Any, List, Optional

import openai
from openai.types.chat import ChatCompletionMessage

from plg.config import get_settings
from plg.llm.base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """An LLM client for interacting with OpenAI's API."""

    def __init__(self) -> None:
        """Initializes the OpenAI client using credentials from settings."""
        settings = get_settings()
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
        self.model_name = settings.MODEL_NAME

    async def acomplete(
        self, prompt: str, tools: Optional[List[Any]] = None
    ) -> ChatCompletionMessage:
        """
        Asynchronously generates a completion for a given prompt using the
        OpenAI API, with optional support for function-calling tools.

        Args:
            prompt: The text prompt to send to the model.
            tools: An optional list of tool schemas for function-calling.

        Returns:
            The message object from the OpenAI API response, which contains
            either the text content or tool call information.
        """
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message
