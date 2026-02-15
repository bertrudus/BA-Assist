"""Prompt templates for requirements document analysis.

Each dimension has its own prompt so they can be tuned independently.
The synthesis prompt combines dimension results into an overall score.
"""

SYSTEM_PROMPT = """\
You are an expert Business Analyst with 20+ years of experience reviewing \
requirements documents across enterprise, government, and startup contexts. \
You are thorough, specific, and constructive. You always back up findings \
with concrete evidence from the document. You return structured JSON only."""

# ---------------------------------------------------------------------------
# Dimension prompts — keyed by dimension name
# ---------------------------------------------------------------------------

DIMENSION_PROMPTS: dict[str, str] = {}

DIMENSION_PROMPTS["completeness"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for COMPLETENESS across these areas:

1. Document structure — are all expected sections present?
   - Business context / problem statement
   - Scope (in-scope and out-of-scope)
   - Stakeholders
   - Functional requirements
   - Non-functional requirements
   - Constraints and assumptions
   - Dependencies
   - Acceptance criteria / success measures

2. Individual requirement completeness:
   - Is each requirement measurable?
   - Is each requirement testable?
   - Does each have a unique identifier?
   - Are edge cases and error scenarios covered?

3. Coverage gaps:
   - Are there obvious missing requirements given the stated scope?
   - Are non-functional concerns addressed (performance, security, accessibility)?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "completeness",
  "score": <0-100>,
  "missing_sections": ["list of missing sections"],
  "incomplete_requirements": [
    {{
      "requirement_id": "REQ-XXX or description",
      "issue": "what is missing",
      "recommendation": "what to add"
    }}
  ],
  "coverage_gaps": ["list of gaps"],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["consistency"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for CONSISTENCY:

1. Contradictions:
   - Do any requirements contradict each other?
   - Are there conflicting constraints or assumptions?

2. Terminology:
   - Is terminology used consistently throughout?
   - Are key terms defined and used uniformly?
   - Are there synonyms used interchangeably that could cause confusion?

3. Duplication:
   - Are there duplicate or overlapping requirements?
   - Are there redundant sections or repeated information?

4. Priority alignment:
   - Do priority levels make sense relative to each other?
   - Are dependencies consistent with stated priorities?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "consistency",
  "score": <0-100>,
  "contradictions": [
    {{
      "requirement_ids": ["REQ-A", "REQ-B"],
      "description": "how they contradict",
      "recommendation": "how to resolve"
    }}
  ],
  "terminology_issues": [
    {{
      "term": "the inconsistent term",
      "occurrences": ["how it appears in different places"],
      "recommendation": "standardise to this"
    }}
  ],
  "duplicates": [
    {{
      "requirement_ids": ["REQ-A", "REQ-B"],
      "description": "what overlaps"
    }}
  ],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["solution_neutrality"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for SOLUTION NEUTRALITY:

1. What vs How:
   - Do requirements describe WHAT the system should do, not HOW?
   - Are there implementation details embedded in requirements?

2. Technology/vendor assumptions:
   - Are specific technologies, platforms, or vendors named unnecessarily?
   - Could requirements be fulfilled by multiple technical solutions?

3. Language:
   - Is implementation language used where business language should be?
   - Are there references to specific UI patterns, database structures, \
or API designs that constrain the solution?

For each violation, provide the original text and a rewritten \
solution-neutral version.
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "solution_neutrality",
  "score": <0-100>,
  "violations": [
    {{
      "requirement_id": "REQ-XXX or description",
      "original_text": "the problematic text",
      "issue": "why this is solution-specific",
      "suggested_rewrite": "solution-neutral alternative"
    }}
  ],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["context_scope_clarity"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for CONTEXT & SCOPE CLARITY:

1. Business problem:
   - Is the business problem or opportunity clearly stated?
   - Is there a clear rationale for why this work is needed?

2. Scope boundaries:
   - Are in-scope items explicitly listed?
   - Are out-of-scope items explicitly listed?
   - Are there ambiguous areas that could lead to scope creep?

3. Stakeholders:
   - Are all stakeholders identified?
   - Are their needs and interests documented?
   - Are roles and responsibilities clear?

4. Success criteria:
   - Is the definition of done / success criteria clear?
   - Are measurable outcomes defined?

5. Assumptions and constraints:
   - Are assumptions documented and reasonable?
   - Are constraints (budget, time, technical, regulatory) stated?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "context_scope_clarity",
  "score": <0-100>,
  "business_problem_assessment": {{
    "is_clear": true/false,
    "issues": ["list of issues if not clear"]
  }},
  "scope_assessment": {{
    "in_scope_defined": true/false,
    "out_of_scope_defined": true/false,
    "ambiguous_areas": ["areas that could cause scope creep"]
  }},
  "stakeholder_assessment": {{
    "identified": true/false,
    "missing_stakeholders": ["potentially missing stakeholders"]
  }},
  "success_criteria_assessment": {{
    "defined": true/false,
    "issues": ["list of issues"]
  }},
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

DIMENSION_PROMPTS["quality"] = """\
<artifact>
{artifact_text}
</artifact>

<evaluation_criteria>
Evaluate the requirements document for cross-cutting QUALITY:

1. Unambiguous language:
   - Flag uses of "should", "might", "could", "etc.", "and/or", \
"appropriate", "relevant", "as needed"
   - Flag vague quantifiers: "fast", "quickly", "many", "large", "small"

2. Atomic requirements:
   - Does each requirement state exactly one thing?
   - Are there compound requirements that should be split?

3. Traceability:
   - Does each requirement have a unique identifier?
   - Is there a consistent numbering/ID scheme?

4. Prioritisation:
   - Are requirements prioritised (MoSCoW or equivalent)?
   - Is the prioritisation scheme consistent?

5. Testability:
   - Can a test be written for each requirement?
   - Are acceptance criteria specific enough to verify?
</evaluation_criteria>

<output_format>
Return ONLY valid JSON:
{{
  "dimension": "quality",
  "score": <0-100>,
  "ambiguous_language": [
    {{
      "requirement_id": "REQ-XXX or description",
      "text": "the ambiguous text",
      "issue": "why it is ambiguous",
      "suggested_rewrite": "clearer alternative"
    }}
  ],
  "non_atomic_requirements": [
    {{
      "requirement_id": "REQ-XXX or description",
      "text": "the compound requirement",
      "suggested_split": ["split requirement 1", "split requirement 2"]
    }}
  ],
  "traceability_issues": ["list of issues"],
  "prioritisation_issues": ["list of issues"],
  "testability_issues": [
    {{
      "requirement_id": "REQ-XXX or description",
      "issue": "why it is not testable",
      "recommendation": "how to make it testable"
    }}
  ],
  "strengths": ["what is done well"],
  "summary": "2-3 sentence overall assessment"
}}
</output_format>"""

# ---------------------------------------------------------------------------
# Synthesis prompt — combines dimension results into overall score
# ---------------------------------------------------------------------------

SYNTHESIS_PROMPT = """\
<dimension_results>
{dimension_results_json}
</dimension_results>

<artifact>
{artifact_text}
</artifact>

<instructions>
You have evaluated a requirements document across five dimensions. \
The individual dimension results are provided above.

Synthesise these results into an overall assessment:

1. Calculate an overall score (0-100) as a weighted average:
   - Completeness: 25%
   - Consistency: 20%
   - Solution Neutrality: 15%
   - Context & Scope Clarity: 20%
   - Quality: 20%

2. Identify the top 3-5 most critical issues across all dimensions.

3. Generate specific, actionable suggestions for improvement. \
For each suggestion, provide:
   - The original text from the artifact
   - A suggested replacement or addition
   - A rationale for the change

4. Provide a brief executive summary (3-5 sentences).

Return ONLY valid JSON matching this structure:
{{
  "overall_score": <0-100>,
  "executive_summary": "3-5 sentence summary",
  "dimension_scores": [
    {{
      "name": "dimension name",
      "score": <0-100>,
      "severity": "INFO|WARNING|CRITICAL",
      "top_findings": ["key findings for this dimension"]
    }}
  ],
  "critical_issues": [
    {{
      "id": "ISSUE-001",
      "dimension": "which dimension",
      "severity": "INFO|WARNING|CRITICAL",
      "description": "what the issue is",
      "location": "where in the artifact",
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

# ---------------------------------------------------------------------------
# Dimension metadata — weights and display info
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS: dict[str, float] = {
    "completeness": 0.25,
    "consistency": 0.20,
    "solution_neutrality": 0.15,
    "context_scope_clarity": 0.20,
    "quality": 0.20,
}

DIMENSION_DISPLAY_NAMES: dict[str, str] = {
    "completeness": "Completeness",
    "consistency": "Consistency",
    "solution_neutrality": "Solution Neutrality",
    "context_scope_clarity": "Context & Scope Clarity",
    "quality": "Quality",
}
