"""User story analyser.

Evaluates user stories for format compliance, persona quality,
acceptance criteria, and INVEST principles.
"""

from ba_analyser.analysers.base import BaseAnalyser
from ba_analyser.models import ArtifactType
from ba_analyser.prompts.user_story_analysis import (
    DIMENSION_DISPLAY_NAMES,
    DIMENSION_PROMPTS,
    SYNTHESIS_PROMPT,
    SYSTEM_PROMPT,
)


class StoryAnalyser(BaseAnalyser):
    """Analyses user story artifacts."""

    @property
    def artifact_type(self) -> ArtifactType:
        return ArtifactType.USER_STORY

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def dimension_prompts(self) -> dict[str, str]:
        return DIMENSION_PROMPTS

    @property
    def synthesis_prompt(self) -> str:
        return SYNTHESIS_PROMPT

    @property
    def dimension_display_names(self) -> dict[str, str]:
        return DIMENSION_DISPLAY_NAMES
