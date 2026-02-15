"""Prompt templates for business process analysis."""

SYSTEM_PROMPT = """\
You are an expert Business Analyst specialising in process modelling and \
improvement. You have deep experience with BPMN, value stream mapping, and \
process optimisation. You are thorough, specific, and constructive. \
You return structured JSON only."""

DIMENSION_PROMPTS: dict[str, str] = {}

DIMENSION_PROMPTS["structure"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the business process for STRUCTURE:

1. Start and end events:
   - Is there a clearly defined start event / trigger?
   - Is there a clearly defined end event / outcome?
   - Are there multiple valid end states? If so, are they all documented?

2. Flow completeness:
   - Are all steps numbered or ordered sequentially?
   - Is there a logical flow from start to end?
   - Are there any orphan steps (unreachable or dead-end)?
   - Can every step be reached from the start event?

3. Process boundaries:
   - Is the scope of the process clear?
   - Are inputs and outputs defined?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "structure",
  "score": <0-100>,
  "start_event": {{"defined": true/false, "description": "..."}},
  "end_event": {{"defined": true/false, "description": "..."}},
  "orphan_steps": ["list of unreachable or dead-end steps"],
  "flow_issues": ["list of flow problems"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["decision_points"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the business process for DECISION POINTS:

1. Decision clarity:
   - Are all decision points (gateways, branches) clearly identified?
   - Does each decision point have defined criteria for each path?
   - Are the criteria unambiguous and testable?

2. Path coverage:
   - Are all possible outcomes of each decision documented?
   - Are there binary decisions that should have more options?
   - Do all decision paths lead somewhere (no dead ends)?

3. Exception and error paths:
   - Are error / exception scenarios documented?
   - Is there a default or fallback path when criteria aren't met?
   - Are timeout or escalation paths defined where appropriate?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "decision_points",
  "score": <0-100>,
  "decision_points": [
    {{
      "step": "step reference",
      "criteria_defined": true/false,
      "paths_complete": true/false,
      "issues": ["list of issues"]
    }}
  ],
  "missing_exception_paths": ["scenarios not covered"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["roles_responsibilities"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the business process for ROLES & RESPONSIBILITIES:

1. Role assignment:
   - Is every step assigned to a role, team, or system?
   - Are the roles clearly defined and distinguishable?
   - Are there steps with ambiguous or missing ownership?

2. Handoffs:
   - Are handoffs between roles/teams/systems explicit?
   - Is it clear what is passed from one role to another?
   - Are there potential bottlenecks at handoff points?

3. RACI clarity:
   - For each step, is it clear who is Responsible?
   - Are there steps where multiple parties could conflict?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "roles_responsibilities",
  "score": <0-100>,
  "unassigned_steps": ["steps without clear ownership"],
  "handoff_issues": [
    {{
      "from_role": "...",
      "to_role": "...",
      "step": "...",
      "issue": "what is unclear"
    }}
  ],
  "roles_identified": ["list of all roles/teams/systems found"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["business_alignment"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the business process for BUSINESS ALIGNMENT:

1. Objective alignment:
   - Does the process clearly serve a stated business objective?
   - Are there steps that don't contribute to the objective?
   - Is the value of the process outcome clear?

2. Efficiency:
   - Are there redundant or unnecessary steps?
   - Are there opportunities for automation or simplification?
   - Are wait states or delays identified and justified?

3. Measurability:
   - Are there defined KPIs or metrics for the process?
   - Can the process be monitored for performance?
   - Are SLAs or time expectations stated for key steps?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "business_alignment",
  "score": <0-100>,
  "objective_clarity": {{"clear": true/false, "issues": ["..."]}},
  "redundant_steps": ["steps that may be unnecessary"],
  "automation_opportunities": ["steps that could be automated"],
  "measurability_issues": ["what cannot be measured"],
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
You have evaluated a business process across four dimensions. \
The individual dimension results are provided above.

Synthesise these results into an overall assessment:

1. Calculate an overall score (0-100) as a weighted average:
   - Structure: 30%
   - Decision Points: 25%
   - Roles & Responsibilities: 25%
   - Business Alignment: 20%

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
      "location": "where in the process",
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
    "structure": "Structure",
    "decision_points": "Decision Points",
    "roles_responsibilities": "Roles & Responsibilities",
    "business_alignment": "Business Alignment",
}
