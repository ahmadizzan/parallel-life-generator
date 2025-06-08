from plg.config import get_settings
from plg.llm.base import BaseLLMClient
from plg.llm.openai_client import OpenAIClient


def get_llm_client() -> BaseLLMClient:
    """
    Factory function to get the appropriate LLM client based on the
    configured provider.

    Raises:
        NotImplementedError: If the configured LLM_PROVIDER is not supported.

    Returns:
        An instance of a class that implements the BaseLLMClient interface.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        return OpenAIClient()

    raise NotImplementedError(
        f"The LLM provider '{settings.LLM_PROVIDER}' is not supported."
    )
