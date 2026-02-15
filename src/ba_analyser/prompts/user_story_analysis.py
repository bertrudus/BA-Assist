"""Prompt templates for user story analysis."""

SYSTEM_PROMPT = """\
You are an expert Agile Business Analyst and Product Owner with deep \
experience writing and reviewing user stories. You evaluate stories \
against industry best practices including INVEST principles. \
You are thorough, specific, and constructive. You return structured JSON only."""

DIMENSION_PROMPTS: dict[str, str] = {}

DIMENSION_PROMPTS["format_compliance"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the user stories for FORMAT COMPLIANCE:

1. Story structure:
   - Does each story follow "As a [persona], I want [goal], so that [benefit]"?
   - Are all three parts (persona, goal, benefit) present and meaningful?
   - Is the benefit a genuine business outcome, not just a restatement of the goal?

2. Consistency:
   - Is the format consistent across all stories?
   - Are stories clearly separated and identifiable?
   - Do stories have unique identifiers?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "format_compliance",
  "score": <0-100>,
  "non_compliant_stories": [
    {{
      "story_id": "...",
      "issue": "what is wrong with the format",
      "recommendation": "how to fix"
    }}
  ],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["persona_quality"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the user stories for PERSONA QUALITY:

1. Specificity:
   - Are personas specific (not generic "user" or "admin" without context)?
   - Do personas represent real stakeholder groups?
   - Is it clear what distinguishes one persona from another?

2. Consistency:
   - Are the same personas used consistently across stories?
   - Are persona names standardised?

3. Coverage:
   - Do the stories cover all relevant user types?
   - Are there stakeholders mentioned elsewhere that lack stories?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "persona_quality",
  "score": <0-100>,
  "personas_found": ["list of personas"],
  "generic_personas": [
    {{
      "story_id": "...",
      "persona": "the generic persona",
      "suggestion": "more specific alternative"
    }}
  ],
  "missing_personas": ["stakeholder groups without stories"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["acceptance_criteria"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the user stories for ACCEPTANCE CRITERIA quality:

1. Presence:
   - Does every story have acceptance criteria?
   - Are there enough criteria to fully define "done"?

2. Testability:
   - Can each criterion be verified with a specific test?
   - Are criteria measurable and unambiguous?
   - Do criteria avoid vague language ("should work well", "fast", etc.)?

3. Completeness:
   - Do criteria cover the happy path?
   - Do criteria cover edge cases and error scenarios?
   - Are boundary conditions addressed?

4. Independence:
   - Are criteria independent of each other?
   - Can each be tested in isolation?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "acceptance_criteria",
  "score": <0-100>,
  "stories_without_criteria": ["story IDs missing AC"],
  "weak_criteria": [
    {{
      "story_id": "...",
      "criterion": "the weak criterion",
      "issue": "why it is weak",
      "suggestion": "stronger alternative"
    }}
  ],
  "missing_edge_cases": [
    {{
      "story_id": "...",
      "scenario": "edge case not covered"
    }}
  ],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["invest_principles"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the user stories against INVEST principles:

1. Independent — Can each story be developed and delivered independently?
2. Negotiable — Is the story flexible enough for discussion, not a contract?
3. Valuable — Does each story deliver value to the user or business?
4. Estimable — Is the story clear enough to estimate effort?
5. Small — Is the story appropriately sized (not too large, not trivial)?
6. Testable — Can the story be verified through testing?

Also check:
- Is there solution language in story bodies (implementation details)?
- Are dependencies between stories identified?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "invest_principles",
  "score": <0-100>,
  "violations": [
    {{
      "story_id": "...",
      "principle": "which INVEST principle",
      "issue": "how it violates",
      "recommendation": "how to fix"
    }}
  ],
  "solution_language": [
    {{
      "story_id": "...",
      "text": "the solution language found",
      "suggestion": "business language alternative"
    }}
  ],
  "dependency_issues": ["missing or unclear dependencies"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

SYNTHESIS_PROMPT = """\
<dimension_results>
{dimension_results_json}
</dimension_results>

<artifact>
{artifact_text}
</artifact>

<instructions>
You have evaluated user stories across four dimensions. \
The individual dimension results are provided above.

Synthesise these results into an overall assessment:

1. Calculate an overall score (0-100) as a weighted average:
   - Format Compliance: 20%
   - Persona Quality: 20%
   - Acceptance Criteria: 35%
   - INVEST Principles: 25%

2. Identify the top 3-5 most critical issues across all dimensions.

3. Generate specific, actionable suggestions for improvement.

Return ONLY valid JSON matching this structure:
{{
  "overall_score": <0-100>,
  "executive_summary": "3-5 sentence summary",
  "dimension_scores": [
    {{
      "name": "dimension name",
      "score": <0-100>,
      "severity": "INFO|WARNING|CRITICAL",
      "top_findings": ["key findings"]
    }}
  ],
  "critical_issues": [
    {{
      "id": "ISSUE-001",
      "dimension": "which dimension",
      "severity": "INFO|WARNING|CRITICAL",
      "description": "what the issue is",
      "location": "which story/section",
      "recommendation": "how to fix it"
    }}
  ],
  "suggestions": [
    {{
      "id": "SUG-001",
      "original_text": "text from the artifact",
      "suggested_text": "improved version",
      "rationale": "why this change helps"
    }}
  ]
}}
</instructions>"""

DIMENSION_DISPLAY_NAMES: dict[str, str] = {
    "format_compliance": "Format Compliance",
    "persona_quality": "Persona Quality",
    "acceptance_criteria": "Acceptance Criteria",
    "invest_principles": "INVEST Principles",
}
