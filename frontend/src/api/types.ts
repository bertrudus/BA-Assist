export type ArtifactType =
  | "requirements_document"
  | "business_process"
  | "user_story"
  | "use_case"
  | "unknown"

export interface DimensionScore {
  name: string
  score: number
  findings: string[]
  severity: "INFO" | "WARNING" | "CRITICAL"
}

export interface Issue {
  id: string
  dimension: string
  severity: "INFO" | "WARNING" | "CRITICAL"
  description: string
  location: string
  recommendation: string
}

export interface Suggestion {
  id: string
  original_text: string
  suggested_text: string
  rationale: string
}

export interface AnalysisResult {
  artifact_type: ArtifactType
  overall_score: number
  dimensions: DimensionScore[]
  issues: Issue[]
  suggestions: Suggestion[]
  iteration_number: number
}

export interface UserStory {
  id: string
  epic: string
  title: string
  persona: string
  goal: string
  benefit: string
  acceptance_criteria: string[]
  priority: "Must" | "Should" | "Could" | "Won't"
  estimate_complexity: "S" | "M" | "L" | "XL"
  dependencies: string[]
  source_requirement_ids: string[]
}

export interface ComparisonReport {
  previous_iteration: number
  current_iteration: number
  previous_score: number
  current_score: number
  score_delta: number
  improved_dimensions: string[]
  regressed_dimensions: string[]
  resolved_issues: string[]
  new_issues: string[]
}

export interface CoverageReport {
  total_requirements: number
  covered_requirements: number
  uncovered_requirements: string[]
  coverage_percentage: number
}

export interface SSEEvent {
  event: string
  data: Record<string, unknown>
}

export interface AppConfig {
  llm_provider: string
  anthropic_model_id: string
  anthropic_api_key_set: boolean
  bedrock_model_id: string
  aws_region: string
  bedrock_max_tokens: number
  bedrock_temperature_analysis: number
  bedrock_temperature_generation: number
  analysis_quality_threshold: number
}
