import { useEffect, useState } from "react"
import { Loader2, CheckCircle2, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

export interface CompletedStep {
  name: string
  score?: number
  completedAt: number
}

interface ProgressStreamProps {
  message: string
  detail?: Record<string, unknown> | null
  completedSteps?: CompletedStep[]
  totalSteps?: number
  startedAt?: number
  onCancel?: () => void
  className?: string
}

function formatElapsed(ms: number): string {
  const secs = Math.floor(ms / 1000)
  const mins = Math.floor(secs / 60)
  const remainSecs = secs % 60
  if (mins > 0) return `${mins}m ${remainSecs}s`
  return `${secs}s`
}

function scoreColor(score: number): string {
  if (score >= 70) return "text-green-600"
  if (score >= 40) return "text-amber-500"
  return "text-red-500"
}

export function ProgressStream({
  message,
  detail,
  completedSteps = [],
  totalSteps,
  startedAt,
  onCancel,
  className,
}: ProgressStreamProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!startedAt) return
    const interval = setInterval(() => {
      setElapsed(Date.now() - startedAt)
    }, 1000)
    return () => clearInterval(interval)
  }, [startedAt])

  const current = detail?.current as number | undefined
  const total = totalSteps || (detail?.total as number | undefined)
  const pct = current && total ? Math.round((current / total) * 100) : undefined
  const isSynthesising = detail?.step === "synthesising"

  return (
    <div className={cn("border border-border rounded-lg p-6 bg-card", className)}>
      {/* Header row: spinner + message + timer */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary shrink-0" />
          <p className="text-sm font-medium">{message}</p>
        </div>
        <div className="flex items-center gap-3">
          {startedAt && (
            <span className="text-xs font-mono text-muted-foreground tabular-nums">
              {formatElapsed(elapsed)}
            </span>
          )}
          {onCancel && (
            <button
              onClick={onCancel}
              className="text-xs text-muted-foreground hover:text-destructive underline"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {pct !== undefined && (
        <div className="mb-4">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Step {current} of {total}
          </p>
        </div>
      )}

      {/* Synthesising gets a pulsing bar since we don't know how long it will take */}
      {isSynthesising && (
        <div className="mb-4">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full animate-pulse w-full opacity-40" />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Combining dimension results into final report — this may take 15-30s
          </p>
        </div>
      )}

      {/* Completed steps */}
      {completedSteps.length > 0 && (
        <div className="space-y-1.5 mt-2">
          {completedSteps.map((step) => (
            <div key={step.name} className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
              <span className="text-muted-foreground">{step.name}</span>
              {step.score !== undefined && (
                <span className={cn("ml-auto font-mono text-xs font-medium", scoreColor(step.score))}>
                  {Math.round(step.score)}
                </span>
              )}
            </div>
          ))}
          {/* Pending steps indicator */}
          {total && completedSteps.length < total && (
            <div className="flex items-center gap-2 text-sm">
              <Circle className="h-4 w-4 text-muted-foreground/30 shrink-0" />
              <span className="text-muted-foreground/50">
                {total - completedSteps.length} remaining...
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
