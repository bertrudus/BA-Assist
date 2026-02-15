"""Tests for artifact type detection."""

import json
from unittest.mock import MagicMock, patch

import pytest

from ba_analyser.detector import detect_artifact_type
from ba_analyser.models import ArtifactType


@pytest.fixture
def mock_client():
    """Create a mock BedrockClient."""
    return MagicMock()


class TestDetectArtifactType:
    def test_detects_requirements_document(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "requirements_document",
            "confidence": 0.95,
            "rationale": "Contains functional and non-functional requirements with IDs.",
            "secondary_types": [],
        }

        result = detect_artifact_type("REQ-001: The system shall...", mock_client)

        assert result == ArtifactType.REQUIREMENTS_DOCUMENT
        mock_client.invoke_structured.assert_called_once()

    def test_detects_business_process(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "business_process",
            "confidence": 0.90,
            "rationale": "Describes a workflow with steps and decision points.",
            "secondary_types": [],
        }

        result = detect_artifact_type("Step 1: Receive order...", mock_client)

        assert result == ArtifactType.BUSINESS_PROCESS

    def test_detects_user_story(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "user_story",
            "confidence": 0.92,
            "rationale": "Uses As a/I want/So that format.",
            "secondary_types": [],
        }

        result = detect_artifact_type("As a user, I want...", mock_client)

        assert result == ArtifactType.USER_STORY

    def test_detects_use_case(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "use_case",
            "confidence": 0.88,
            "rationale": "Contains actors, preconditions, and main flow.",
            "secondary_types": [],
        }

        result = detect_artifact_type("Actor: Customer\nPrecondition:...", mock_client)

        assert result == ArtifactType.USE_CASE

    def test_returns_unknown_for_unrecognised_type(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "something_weird",
            "confidence": 0.30,
            "rationale": "Could not classify.",
            "secondary_types": [],
        }

        result = detect_artifact_type("Random text...", mock_client)

        assert result == ArtifactType.UNKNOWN

    def test_returns_unknown_when_type_missing(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "confidence": 0.10,
            "rationale": "Could not determine.",
        }

        result = detect_artifact_type("Random text...", mock_client)

        assert result == ArtifactType.UNKNOWN

    def test_passes_low_temperature(self, mock_client):
        mock_client.invoke_structured.return_value = {
            "artifact_type": "requirements_document",
            "confidence": 0.95,
            "rationale": "Test.",
            "secondary_types": [],
        }

        detect_artifact_type("Some text", mock_client)

        call_kwargs = mock_client.invoke_structured.call_args
        assert call_kwargs.kwargs["temperature"] == 0.0
