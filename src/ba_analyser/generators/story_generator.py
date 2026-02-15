"""Story generator — converts validated requirements into structured user stories."""

import json
import logging

from pydantic import ValidationError

from ba_analyser.bedrock_client import BedrockClient
from ba_analyser.models import CoverageReport, UserStory
from ba_analyser.prompts.story_generation import (
    EXTRACT_REQUIREMENTS_PROMPT,
    GENERATE_STORIES_PROMPT,
    IDENTIFY_PERSONAS_PROMPT,
    REFINE_STORY_PROMPT,
    SYSTEM_PROMPT,
    VALIDATE_COVERAGE_PROMPT,
)

logger = logging.getLogger(__name__)


class StoryGenerator:
    """Converts validated requirements into structured user stories."""

    def __init__(self, client: BedrockClient) -> None:
        self.client = client

    def generate(self, requirements_text: str) -> list[UserStory]:
        """Generate user stories from a requirements document.

        Prompt chain:
        1. Extract distinct requirements
        2. Identify personas from stakeholder/context sections
        3. Generate stories grouped into epics with AC, priority, complexity
        """
        # Step 1: Extract requirements
        logger.info("Extracting requirements from document")
        requirements = self._extract_requirements(requirements_text)

        # Step 2: Identify personas
        logger.info("Identifying personas")
        personas = self._identify_personas(requirements_text, requirements)

        # Step 3: Generate stories
        logger.info("Generating user stories")
        raw_stories = self._generate_stories(
            requirements_text, requirements, personas
        )

        # Step 4: Parse into UserStory models
        return self._parse_stories(raw_stories)

    def validate_coverage(
        self,
        requirements_text: str,
        stories: list[UserStory],
    ) -> CoverageReport:
        """Check that all requirements are covered by at least one story."""
        # Extract requirements for comparison
        requirements = self._extract_requirements(requirements_text)

        stories_json = json.dumps(
            [s.model_dump() for s in stories], indent=2
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": VALIDATE_COVERAGE_PROMPT.format(
                            requirements_json=json.dumps(requirements, indent=2),
                            stories_json=stories_json,
                        )
                    }
                ],
            }
        ]

        result = self.client.invoke_structured(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=self.client.config.bedrock_temperature_analysis,
        )

        uncovered = [
            item.get("requirement_id", "")
            for item in result.get("uncovered_requirements", [])
        ]

        return CoverageReport(
            total_requirements=result.get("total_requirements", 0),
            covered_requirements=result.get("covered_requirements", 0),
            uncovered_requirements=uncovered,
            coverage_percentage=result.get("coverage_percentage", 0),
        )

    def refine_story(
        self, story: UserStory, feedback: str
    ) -> UserStory:
        """Iteratively refine a single story based on user feedback."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": REFINE_STORY_PROMPT.format(
                            story_json=story.model_dump_json(indent=2),
                            feedback=feedback,
                        )
                    }
                ],
            }
        ]

        result = self.client.invoke_structured(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=self.client.config.bedrock_temperature_generation,
        )

        return UserStory(**result)

    def _extract_requirements(self, requirements_text: str) -> dict:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": EXTRACT_REQUIREMENTS_PROMPT.format(
                            artifact_text=requirements_text
                        )
                    }
                ],
            }
        ]

        return self.client.invoke_structured(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=self.client.config.bedrock_temperature_analysis,
        )

    def _identify_personas(
        self, requirements_text: str, requirements: dict
    ) -> dict:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": IDENTIFY_PERSONAS_PROMPT.format(
                            artifact_text=requirements_text,
                            requirements_json=json.dumps(requirements, indent=2),
                        )
                    }
                ],
            }
        ]

        return self.client.invoke_structured(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=self.client.config.bedrock_temperature_analysis,
        )

    def _generate_stories(
        self,
        requirements_text: str,
        requirements: dict,
        personas: dict,
    ) -> dict:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": GENERATE_STORIES_PROMPT.format(
                            artifact_text=requirements_text,
                            requirements_json=json.dumps(requirements, indent=2),
                            personas_json=json.dumps(personas, indent=2),
                        )
                    }
                ],
            }
        ]

        return self.client.invoke_structured(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=self.client.config.bedrock_temperature_generation,
        )

    def _parse_stories(self, raw: dict) -> list[UserStory]:
        """Parse raw story JSON into validated UserStory models."""
        stories: list[UserStory] = []
        for story_data in raw.get("stories", []):
            try:
                stories.append(UserStory(**story_data))
            except ValidationError as exc:
                logger.warning(
                    "Skipping invalid story %s: %s",
                    story_data.get("id", "???"),
                    exc,
                )
        return stories
