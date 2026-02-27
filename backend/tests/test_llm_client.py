"""
Unit tests for services/llm/client.py — JSON output parsing logic.

The LLM network call (litellm.acompletion) is mocked so tests run offline
and focus on the client's parsing and fence-stripping behaviour.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.llm.client import LLMClient


def _mock_completion(content: str):
    """Build a minimal litellm-style response object with the given content."""
    response = MagicMock()
    response.choices[0].message.content = content
    return response


@pytest.fixture
def llm_client():
    return LLMClient()


class TestCompleteWithJsonOutput:
    async def test_parses_clean_json(self, llm_client):
        payload = {"risk": "low", "score": 2}
        mock_resp = _mock_completion(json.dumps(payload))

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            result = await llm_client.complete_with_json_output("sys", "user")

        assert result == payload

    async def test_strips_json_markdown_fence(self, llm_client):
        payload = {"summary": "all good"}
        fenced = f"```json\n{json.dumps(payload)}\n```"
        mock_resp = _mock_completion(fenced)

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            result = await llm_client.complete_with_json_output("sys", "user")

        assert result == payload

    async def test_strips_plain_markdown_fence(self, llm_client):
        payload = {"flag": True}
        fenced = f"```\n{json.dumps(payload)}\n```"
        mock_resp = _mock_completion(fenced)

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            result = await llm_client.complete_with_json_output("sys", "user")

        assert result == payload

    async def test_raises_on_invalid_json(self, llm_client):
        mock_resp = _mock_completion("This is not JSON at all.")

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            with pytest.raises(json.JSONDecodeError):
                await llm_client.complete_with_json_output("sys", "user")

    async def test_complete_returns_raw_string(self, llm_client):
        mock_resp = _mock_completion("Hello, world!")

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            result = await llm_client.complete("sys", "user")

        assert result == "Hello, world!"

    async def test_model_string_passed_to_litellm(self, llm_client):
        mock_resp = _mock_completion("{}")

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)) as mock_call:
            await llm_client.complete("sys", "user")

        call_kwargs = mock_call.call_args
        assert call_kwargs.kwargs["model"] == llm_client.model

    async def test_json_with_nested_structure(self, llm_client):
        payload = {
            "findings": [{"clause": "3.2", "risk": "medium"}],
            "overall_risk": "medium",
        }
        fenced = f"```json\n{json.dumps(payload)}\n```"
        mock_resp = _mock_completion(fenced)

        with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
            result = await llm_client.complete_with_json_output("sys", "user")

        assert result["overall_risk"] == "medium"
        assert len(result["findings"]) == 1
