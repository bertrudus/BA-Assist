"""Artifact type detection using Bedrock."""

import logging

from ba_analyser.bedrock_client import BedrockClient
from ba_analyser.models import ArtifactType

logger = logging.getLogger(__name__)

DETECTION_SYSTEM_PROMPT = """\
You are a Business Analysis expert. Your task is to classify a document \
into exactly one artifact type. Return ONLY valid JSON."""

DETECTION_USER_PROMPT = """\
<artifact>
{artifact_text}
</artifact>

<instructions>
Classify this document into one of the following artifact types:

- requirements_document: A document specifying what a system should do. \
Contains functional/non-functional requirements, scope, stakeholders, etc.
- business_process: A description of a business workflow or process. \
Contains steps, decision points, roles, swim lanes, etc.
- user_story: One or more user stories in "As a... I want... So that..." format \
with acceptance criteria.
- use_case: A use case specification with actors, preconditions, main flow, \
alternative flows, postconditions.
- unknown: The document does not clearly fit any of the above categories.

If the document contains elements of multiple types, classify it by its \
PRIMARY purpose. If it is predominantly one type with minor elements of \
another, classify it as the dominant type.

Return ONLY valid JSON:
{{
  "artifact_type": "<one of the types listed above>",
  "confidence": <0.0-1.0>,
  "rationale": "Brief explanation of why this classification was chosen",
  "secondary_types": ["any other types partially present"]
}}
</instructions>"""


def detect_artifact_type(
    artifact_text: str,
    client: BedrockClient,
) -> ArtifactType:
    """Classify a BA artifact into an ArtifactType.

    Args:
        artifact_text: The full text of the artifact to classify.
        client: Configured BedrockClient instance.

    Returns:
        The detected ArtifactType.
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"text": DETECTION_USER_PROMPT.format(artifact_text=artifact_text)}
            ],
        }
    ]

    result = client.invoke_structured(
        messages=messages,
        system=DETECTION_SYSTEM_PROMPT,
        temperature=0.0,
        max_tokens=256,
    )

    raw_type = result.get("artifact_type", "unknown")
    confidence = result.get("confidence", 0.0)

    logger.info(
        "Detected artifact type: %s (confidence: %.2f)", raw_type, confidence
    )

    try:
        return ArtifactType(raw_type)
    except ValueError:
        logger.warning("Unknown artifact type from model: %s", raw_type)
        return ArtifactType.UNKNOWN
