import pytest
from unittest.mock import MagicMock

from pydantic import SecretStr

from plg.config import Settings
from plg.llm.factory import get_llm_client


def test_get_llm_client_returns_openai_client(monkeypatch):
    """
    Verify that get_llm_client returns an OpenAIClient when the provider
    is set to 'openai'.
    """
    # Arrange
    mock_settings = Settings(
        OPENAI_API_KEY=SecretStr("fake-key"), LLM_PROVIDER="openai"
    )
    monkeypatch.setattr("plg.llm.factory.get_settings", lambda: mock_settings)
    # Also mock the OpenAIClient's __init__ to avoid its own setup logic
    monkeypatch.setattr("plg.llm.factory.OpenAIClient", MagicMock())

    # Act
    client = get_llm_client()

    # Assert
    assert isinstance(client, MagicMock)  # It's a mock of OpenAIClient


def test_get_llm_client_raises_for_unsupported_provider(monkeypatch):
    """
    Verify that get_llm_client raises a NotImplementedError for an
    unsupported provider.
    """
    # Arrange
    mock_settings = Settings(
        OPENAI_API_KEY=SecretStr("fake-key"), LLM_PROVIDER="anthropic"
    )
    monkeypatch.setattr("plg.llm.factory.get_settings", lambda: mock_settings)

    # Act & Assert
    with pytest.raises(NotImplementedError) as excinfo:
        get_llm_client()

    assert "anthropic' is not supported" in str(excinfo.value)
