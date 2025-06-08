from abc import ABC, abstractmethod
from typing import Any, List, Optional


class BaseLLMClient(ABC):
    """Abstract base class for a Large Language Model client."""

    @abstractmethod
    async def acomplete(self, prompt: str, tools: Optional[List[Any]] = None) -> Any:
        """
        Asynchronously generates a completion for a given prompt.

        Args:
            prompt: The text prompt to send to the model.
            tools: An optional list of tools the model can call. The structure
                   of a tool is specific to the implementing client.

        Returns:
            The model's response. This could be a string with the text completion,
            or a structured object representing a tool call.
        """
        pass
