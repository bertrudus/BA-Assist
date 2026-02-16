import type { AnalysisResult, ComparisonReport } from "@/api/types"
import { ScoreGauge, ScoreBar } from "@/components/shared/ScoreGauge"
import { ArrowUp, ArrowDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface CompareViewProps {
  result1: AnalysisResult
  result2: AnalysisResult
  comparison: ComparisonReport
}

export function CompareView({ result1, result2, comparison }: CompareViewProps) {
  return (
    <div className="space-y-8">
      {/* Score comparison */}
      <div className="flex items-center justify-center gap-12">
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-2">Artifact 1</p>
          <ScoreGauge score={result1.overall_score} size="lg" />
        </div>
        <div className="text-center">
          <ScoreDelta delta={comparison.score_delta} />
        </div>
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-2">Artifact 2</p>
          <ScoreGauge score={result2.overall_score} size="lg" />
        </div>
      </div>

      {/* Dimensions side by side */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Dimension Comparison</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Artifact 1</p>
            {result1.dimensions.map((d) => (
              <ScoreBar key={d.name} score={d.score} label={d.name} />
            ))}
          </div>
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">Artifact 2</p>
            {result2.dimensions.map((d) => (
              <ScoreBar key={d.name} score={d.score} label={d.name} />
            ))}
          </div>
        </div>
      </div>

      {/* Changes */}
      <div className="grid grid-cols-2 gap-6">
        {comparison.improved_dimensions.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-600 mb-2">Improved</h4>
            <ul className="space-y-1">
              {comparison.improved_dimensions.map((d) => (
                <li key={d} className="text-sm flex items-center gap-2">
                  <ArrowUp className="h-3 w-3 text-green-600" /> {d}
                </li>
              ))}
            </ul>
          </div>
        )}
        {comparison.regressed_dimensions.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-600 mb-2">Regressed</h4>
            <ul className="space-y-1">
              {comparison.regressed_dimensions.map((d) => (
                <li key={d} className="text-sm flex items-center gap-2">
                  <ArrowDown className="h-3 w-3 text-red-600" /> {d}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Issues delta */}
      <div className="grid grid-cols-2 gap-6">
        {comparison.resolved_issues.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-600 mb-2">
              Resolved Issues ({comparison.resolved_issues.length})
            </h4>
            <ul className="space-y-1">
              {comparison.resolved_issues.map((id) => (
                <li key={id} className="text-xs font-mono text-muted-foreground">{id}</li>
              ))}
            </ul>
          </div>
        )}
        {comparison.new_issues.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-600 mb-2">
              New Issues ({comparison.new_issues.length})
            </h4>
            <ul className="space-y-1">
              {comparison.new_issues.map((id) => (
                <li key={id} className="text-xs font-mono text-muted-foreground">{id}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function ScoreDelta({ delta }: { delta: number }) {
  const Icon = delta > 0 ? ArrowUp : delta < 0 ? ArrowDown : Minus
  return (
    <div className={cn(
      "flex flex-col items-center gap-1",
      delta > 0 ? "text-green-600" : delta < 0 ? "text-red-600" : "text-muted-foreground",
    )}>
      <Icon className="h-6 w-6" />
      <span className="text-2xl font-bold">
        {delta > 0 ? "+" : ""}{Math.round(delta)}
      </span>
      <span className="text-xs">points</span>
    </div>
  )
}
