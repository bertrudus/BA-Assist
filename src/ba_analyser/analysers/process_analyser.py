"""Business process analyser.

Evaluates business processes for structure, decision points,
roles & responsibilities, and business alignment.
"""

from ba_analyser.analysers.base import BaseAnalyser
from ba_analyser.models import ArtifactType
from ba_analyser.prompts.process_analysis import (
    DIMENSION_DISPLAY_NAMES,
    DIMENSION_PROMPTS,
    SYNTHESIS_PROMPT,
    SYSTEM_PROMPT,
)


class ProcessAnalyser(BaseAnalyser):
    """Analyses business process artifacts."""

    @property
    def artifact_type(self) -> ArtifactType:
        return ArtifactType.BUSINESS_PROCESS

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
