"""Requirements document analyser.

Evaluates requirements against five dimensions using a prompt chain,
then synthesises results into an overall AnalysisResult.
"""

from ba_analyser.analysers.base import BaseAnalyser
from ba_analyser.models import ArtifactType
from ba_analyser.prompts.requirements_analysis import (
    DIMENSION_DISPLAY_NAMES,
    DIMENSION_PROMPTS,
    SYNTHESIS_PROMPT,
    SYSTEM_PROMPT,
)


class RequirementsAnalyser(BaseAnalyser):
    """Analyses requirements documents against quality dimensions."""

    @property
    def artifact_type(self) -> ArtifactType:
        return ArtifactType.REQUIREMENTS_DOCUMENT

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
