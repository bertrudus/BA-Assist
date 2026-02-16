import type { AnalysisResult } from "@/api/types"
import { ScoreGauge, ScoreBar } from "@/components/shared/ScoreGauge"
import { IssuesTable } from "./IssuesTable"
import { SuggestionsList } from "./SuggestionsList"

interface AnalysisReportProps {
  result: AnalysisResult
  onSuggestionAction?: (ids: string[]) => void
}

export function AnalysisReport({ result, onSuggestionAction }: AnalysisReportProps) {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start gap-6">
        <ScoreGauge score={result.overall_score} size="lg" label="Overall Score" />
        <div className="flex-1">
          <h2 className="text-xl font-bold">Analysis Report</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Artifact type:{" "}
            <span className="font-medium text-foreground">
              {result.artifact_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          </p>
          <p className="text-sm text-muted-foreground">
            Iteration: {result.iteration_number} | Issues: {result.issues.length} | Suggestions: {result.suggestions.length}
          </p>
        </div>
      </div>

      {/* Dimension scores */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Dimension Scores</h3>
        <div className="grid gap-3">
          {result.dimensions.map((dim) => (
            <div key={dim.name} className="bg-card border border-border rounded-lg p-4">
              <ScoreBar score={dim.score} label={dim.name} />
              {dim.findings.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {dim.findings.map((f, i) => (
                    <li key={i} className="text-xs text-muted-foreground pl-2 border-l-2 border-border">
                      {f}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Issues */}
      {result.issues.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Issues ({result.issues.length})</h3>
          <IssuesTable issues={result.issues} />
        </div>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Suggestions ({result.suggestions.length})</h3>
          <SuggestionsList
            suggestions={result.suggestions}
            onApply={onSuggestionAction}
          />
        </div>
      )}
    </div>
  )
}
