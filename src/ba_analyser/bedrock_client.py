"""Wrapper around Amazon Bedrock Runtime for Claude model invocation."""

import json
import logging

import boto3
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from ba_analyser.config import Settings

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Check if a Bedrock error is transient and worth retrying."""
    if isinstance(exc, ClientError):
        code = exc.response["Error"]["Code"]
        return code in (
            "ThrottlingException",
            "ServiceUnavailableException",
            "ModelTimeoutException",
        )
    return False


class BedrockClient:
    """Client for invoking Claude on Amazon Bedrock via the Converse API."""

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or Settings()
        session_kwargs: dict = {"region_name": self.config.aws_region}
        if self.config.aws_profile:
            session_kwargs["profile_name"] = self.config.aws_profile
        session = boto3.Session(**session_kwargs)
        self._client = session.client("bedrock-runtime")

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def invoke(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send messages to Claude via Bedrock Converse API and return the response text.

        Args:
            messages: Conversation messages in Converse API format
                      e.g. [{"role": "user", "content": [{"text": "Hello"}]}]
            system: Optional system prompt.
            temperature: Sampling temperature override.
            max_tokens: Max tokens override.

        Returns:
            The assistant's response text.
        """
        kwargs: dict = {
            "modelId": self.config.bedrock_model_id,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens or self.config.bedrock_max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.config.bedrock_temperature_analysis,
            },
        }
        if system:
            kwargs["system"] = [{"text": system}]

        logger.debug("Invoking Bedrock model %s", self.config.bedrock_model_id)
        response = self._client.converse(**kwargs)

        output = response["output"]["message"]
        text_parts = [
            block["text"] for block in output["content"] if "text" in block
        ]
        return "\n".join(text_parts)

    def invoke_structured(
        self,
        messages: list[dict],
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """Invoke Claude and parse the response as JSON.

        Same parameters as invoke(). Raises ValueError if the response
        is not valid JSON.
        """
        raw = self.invoke(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from Bedrock response: %s", raw[:200])
            raise ValueError(
                f"Bedrock response was not valid JSON: {exc}"
            ) from exc
