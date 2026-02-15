"""Prompt templates for converting requirements into user stories."""

SYSTEM_PROMPT = """\
You are an expert Agile Product Owner and Business Analyst. \
You convert validated requirements into well-structured, development-ready \
user stories following industry best practices. \
You return structured JSON only."""

EXTRACT_REQUIREMENTS_PROMPT = """\
<artifact>
{artifact_text}
</artifact>

<instructions>
Extract all distinct requirements from this document. For each requirement, \
capture its ID (if present), description, and type (functional / non-functional).

Return ONLY valid JSON:
{{
  "requirements": [
    {{
      "id": "REQ-XXX or generated ID",
      "description": "the requirement text",
      "type": "functional|non_functional",
      "section": "which section it came from"
    }}
  ]
}}
</instructions>"""

IDENTIFY_PERSONAS_PROMPT = """\
<artifact>
{artifact_text}
</artifact>

<requirements>
{requirements_json}
</requirements>

<instructions>
Identify all user personas / stakeholder roles from the document and \
extracted requirements. For each persona, describe who they are and \
what their primary needs are.

Return ONLY valid JSON:
{{
  "personas": [
    {{
      "name": "specific persona name (e.g. 'Online Customer', 'Warehouse Manager')",
      "description": "who this persona is",
      "primary_needs": ["their key needs from the system"],
      "related_requirement_ids": ["REQ-IDs relevant to this persona"]
    }}
  ]
}}
</instructions>"""

GENERATE_STORIES_PROMPT = """\
<artifact>
{artifact_text}
</artifact>

<requirements>
{requirements_json}
</requirements>

<personas>
{personas_json}
</personas>

<instructions>
Generate structured user stories from the requirements and personas. \
Group related stories into epics.

For each story:
1. Follow "As a [persona], I want [goal], so that [benefit]" format
2. Write specific, testable acceptance criteria
3. Assign MoSCoW priority (Must, Should, Could, Won't)
4. Estimate relative complexity (S, M, L, XL)
5. Identify dependencies on other stories
6. Trace back to source requirement IDs

Return ONLY valid JSON:
{{
  "epics": [
    {{
      "name": "epic name",
      "description": "epic description"
    }}
  ],
  "stories": [
    {{
      "id": "US-001",
      "epic": "epic name",
      "title": "short title",
      "persona": "the persona name",
      "goal": "what the user wants to do",
      "benefit": "why they want it (business value)",
      "acceptance_criteria": [
        "Given/When/Then or simple testable statement"
      ],
      "priority": "Must|Should|Could|Won't",
      "estimate_complexity": "S|M|L|XL",
      "dependencies": ["US-XXX IDs this depends on"],
      "source_requirement_ids": ["REQ-XXX IDs this covers"]
    }}
  ]
}}
</instructions>"""

VALIDATE_COVERAGE_PROMPT = """\
<requirements>
{requirements_json}
</requirements>

<stories>
{stories_json}
</stories>

<instructions>
Check that every requirement is covered by at least one user story. \
Identify any requirements that are not addressed.

Return ONLY valid JSON:
{{
  "total_requirements": <count>,
  "covered_requirements": <count>,
  "coverage_percentage": <0-100>,
  "uncovered_requirements": [
    {{
      "requirement_id": "REQ-XXX",
      "description": "what the requirement says",
      "suggestion": "how it could be covered"
    }}
  ],
  "over_covered_requirements": [
    {{
      "requirement_id": "REQ-XXX",
      "story_ids": ["US-001", "US-002"],
      "note": "covered by multiple stories — verify no duplication"
    }}
  ]
}}
</instructions>"""

REFINE_STORY_PROMPT = """\
<story>
{story_json}
</story>

<feedback>
{feedback}
</feedback>

<instructions>
Refine the user story based on the feedback provided. \
Maintain the same JSON structure but improve the content.

Return ONLY valid JSON with the same structure as the input story:
{{
  "id": "...",
  "epic": "...",
  "title": "...",
  "persona": "...",
  "goal": "...",
  "benefit": "...",
  "acceptance_criteria": ["..."],
  "priority": "Must|Should|Could|Won't",
  "estimate_complexity": "S|M|L|XL",
  "dependencies": ["..."],
  "source_requirement_ids": ["..."]
}}
</instructions>"""
