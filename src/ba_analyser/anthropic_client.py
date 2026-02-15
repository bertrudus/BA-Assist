"""Wrapper around the Anthropic Messages API for direct API access."""

import json
import logging

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ba_analyser.config import Settings

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for invoking Claude via the Anthropic Messages API.

    Drop-in replacement for BedrockClient when using Anthropic API keys
    instead of AWS Bedrock.
    """

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or Settings()
        self._client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)

    @retry(
        retry=retry_if_exception_type(
            (anthropic.RateLimitError, anthropic.APIStatusError)
        ),
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
        """Send messages to Claude via the Anthropic Messages API.

        Args:
            messages: Conversation messages in Anthropic format
                      e.g. [{"role": "user", "content": "Hello"}]
            system: Optional system prompt.
            temperature: Sampling temperature override.
            max_tokens: Max tokens override.

        Returns:
            The assistant's response text.
        """
        # Normalise messages: Bedrock Converse format uses
        # [{"text": "..."}] content blocks, Anthropic API accepts
        # both string and list-of-blocks content.
        normalised = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                # Extract text from content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
                content = "\n".join(parts)
            normalised.append({"role": msg["role"], "content": content})

        kwargs: dict = {
            "model": self.config.anthropic_model_id,
            "messages": normalised,
            "max_tokens": max_tokens or self.config.bedrock_max_tokens,
            "temperature": temperature
            if temperature is not None
            else self.config.bedrock_temperature_analysis,
        }
        if system:
            kwargs["system"] = system

        logger.debug("Invoking Anthropic model %s", self.config.anthropic_model_id)
        response = self._client.messages.create(**kwargs)

        text_parts = [
            block.text for block in response.content if block.type == "text"
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
            logger.error("Failed to parse JSON from Anthropic response: %s", raw[:200])
            raise ValueError(
                f"Anthropic response was not valid JSON: {exc}"
            ) from exc
