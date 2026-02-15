"""Tests for BedrockClient."""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from ba_analyser.bedrock_client import BedrockClient
from ba_analyser.config import Settings


@pytest.fixture
def settings():
    return Settings(
        aws_region="us-east-1",
        aws_profile=None,
        bedrock_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        bedrock_max_tokens=1024,
        bedrock_temperature_analysis=0.1,
    )


@pytest.fixture
def mock_boto_client():
    return MagicMock()


@pytest.fixture
def client(settings, mock_boto_client):
    with patch("ba_analyser.bedrock_client.boto3.Session") as mock_session:
        mock_session.return_value.client.return_value = mock_boto_client
        return BedrockClient(config=settings)


def _converse_response(text: str) -> dict:
    """Build a mock Converse API response."""
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": text}],
            }
        }
    }


class TestBedrockClientInvoke:
    def test_invoke_returns_text(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = _converse_response("Hello world")

        result = client.invoke(
            messages=[{"role": "user", "content": [{"text": "Hi"}]}]
        )

        assert result == "Hello world"

    def test_invoke_passes_system_prompt(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = _converse_response("OK")

        client.invoke(
            messages=[{"role": "user", "content": [{"text": "Hi"}]}],
            system="Be helpful.",
        )

        call_kwargs = mock_boto_client.converse.call_args.kwargs
        assert call_kwargs["system"] == [{"text": "Be helpful."}]

    def test_invoke_uses_default_temperature(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = _converse_response("OK")

        client.invoke(
            messages=[{"role": "user", "content": [{"text": "Hi"}]}]
        )

        call_kwargs = mock_boto_client.converse.call_args.kwargs
        assert call_kwargs["inferenceConfig"]["temperature"] == 0.1

    def test_invoke_overrides_temperature(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = _converse_response("OK")

        client.invoke(
            messages=[{"role": "user", "content": [{"text": "Hi"}]}],
            temperature=0.7,
        )

        call_kwargs = mock_boto_client.converse.call_args.kwargs
        assert call_kwargs["inferenceConfig"]["temperature"] == 0.7

    def test_invoke_joins_multiple_text_blocks(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Part 1"}, {"text": "Part 2"}],
                }
            }
        }

        result = client.invoke(
            messages=[{"role": "user", "content": [{"text": "Hi"}]}]
        )

        assert result == "Part 1\nPart 2"


class TestBedrockClientInvokeStructured:
    def test_parses_json(self, client, mock_boto_client):
        data = {"score": 85, "summary": "Good"}
        mock_boto_client.converse.return_value = _converse_response(
            json.dumps(data)
        )

        result = client.invoke_structured(
            messages=[{"role": "user", "content": [{"text": "Analyse"}]}]
        )

        assert result == data

    def test_strips_markdown_code_fences(self, client, mock_boto_client):
        data = {"score": 85}
        wrapped = f"```json\n{json.dumps(data)}\n```"
        mock_boto_client.converse.return_value = _converse_response(wrapped)

        result = client.invoke_structured(
            messages=[{"role": "user", "content": [{"text": "Analyse"}]}]
        )

        assert result == data

    def test_raises_on_invalid_json(self, client, mock_boto_client):
        mock_boto_client.converse.return_value = _converse_response(
            "This is not JSON"
        )

        with pytest.raises(ValueError, match="not valid JSON"):
            client.invoke_structured(
                messages=[{"role": "user", "content": [{"text": "Analyse"}]}]
            )
