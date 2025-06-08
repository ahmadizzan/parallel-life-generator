import pytest
from unittest.mock import AsyncMock, MagicMock

from pydantic import SecretStr
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice

from plg.config import Settings
from plg.llm.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_simple_call_returns_non_empty_text(monkeypatch):
    """
    Verify that a simple call to acomplete returns a message with non-empty text.
    """
    # Arrange
    # 1. Mock settings to avoid dependency on environment variables
    mock_settings = Settings(
        OPENAI_API_KEY=SecretStr("fake-api-key"),
        LLM_PROVIDER="openai",
        MODEL_NAME="gpt-4-turbo-preview",
    )
    monkeypatch.setattr("plg.llm.openai_client.get_settings", lambda: mock_settings)

    # 2. Prepare the mock response from the API
    mock_choice = Choice(
        finish_reason="stop",
        index=0,
        message=ChatCompletionMessage(
            role="assistant", content="This is a test response."
        ),
    )
    mock_completion = ChatCompletion(
        id="chatcmpl-test",
        choices=[mock_choice],
        created=1677652288,
        model=mock_settings.MODEL_NAME,
        object="chat.completion",
    )

    # 3. Mock the entire AsyncOpenAI client that gets instantiated
    mock_async_openai_instance = MagicMock()
    mock_async_openai_instance.chat.completions.create = AsyncMock(
        return_value=mock_completion
    )
    monkeypatch.setattr(
        "plg.llm.openai_client.openai.AsyncOpenAI",
        lambda api_key: mock_async_openai_instance,
    )

    # Act
    client = OpenAIClient()
    result = await client.acomplete(prompt="Hello, world!")

    # Assert
    assert isinstance(result, ChatCompletionMessage)
    assert result.content == "This is a test response."
    mock_async_openai_instance.chat.completions.create.assert_called_once_with(
        model=mock_settings.MODEL_NAME,
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
