import { useCallback, useRef, useState } from "react"
import { FileUpload } from "@/components/shared/FileUpload"
import { ProgressStream, type CompletedStep } from "@/components/shared/ProgressStream"
import { AnalysisReport } from "@/components/analysis/AnalysisReport"
import { useSSE } from "@/hooks/useSSE"
import { api } from "@/api/client"
import type { AnalysisResult, ComparisonReport, SSEEvent } from "@/api/types"
import { ArrowUp, ArrowDown, CheckCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface IterationResult {
  result: AnalysisResult
  comparison?: ComparisonReport
  is_ready: boolean
}

export function IteratePage() {
  const [sessionId, setSessionId] = useState("")
  const [artifactText, setArtifactText] = useState("")
  const [threshold, setThreshold] = useState(80)
  const [history, setHistory] = useState<{ iteration: number; score: number }[]>([])
  const [isReady, setIsReady] = useState(false)
  const [comparison, setComparison] = useState<ComparisonReport | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [editText, setEditText] = useState("")
  const [applying, setApplying] = useState(false)
  const [completedSteps, setCompletedSteps] = useState<CompletedStep[]>([])
  const [totalSteps, setTotalSteps] = useState<number | undefined>()
  const startedAtRef = useRef<number>(0)

  const analysis = useSSE<IterationResult>()

  const handleProgress = useCallback((event: SSEEvent) => {
    if (event.event === "progress" && event.data.total) {
      setTotalSteps(event.data.total as number)
    }
    if (event.event === "dimension_complete") {
      setCompletedSteps((prev) => [
        ...prev,
        {
          name: event.data.dimension as string,
          score: event.data.score as number,
          completedAt: Date.now(),
        },
      ])
    }
  }, [])

  const startSession = async (text: string) => {
    setArtifactText(text)
    const session = await api.createSession(text, threshold)
    setSessionId(session.id)
    runAnalysis(session.id)
  }

  const runAnalysis = (sid?: string) => {
    const id = sid || sessionId
    setCompletedSteps([])
    setTotalSteps(undefined)
    startedAtRef.current = Date.now()
    analysis.start(
      `/api/sessions/${id}/analyse`,
      {},
      {
        extractResult: (event) => event.data as unknown as IterationResult,
        onProgress: handleProgress,
      },
    )
  }

  // When analysis completes, update state
  const result = analysis.result
  if (result && history.length < (result.result?.iteration_number || 0)) {
    const newEntry = {
      iteration: result.result.iteration_number,
      score: result.result.overall_score,
    }
    setHistory((prev) => [...prev, newEntry])
    setIsReady(result.is_ready)
    setComparison(result.comparison || null)
  }

  const handleApplySuggestions = async (ids: string[]) => {
    if (!sessionId || ids.length === 0) return
    setApplying(true)
    try {
      const { artifact_text } = await api.applySuggestions(sessionId, ids)
      setArtifactText(artifact_text)
      runAnalysis()
    } finally {
      setApplying(false)
    }
  }

  const handleSaveEdit = async () => {
    if (!sessionId) return
    await api.updateArtifact(sessionId, editText)
    setArtifactText(editText)
    setEditMode(false)
    runAnalysis()
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Iterate</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Iteratively improve your artifact: analyse, review, revise, repeat.
        </p>
      </div>

      {!sessionId ? (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">Target Score</label>
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              min={0}
              max={100}
              className="border border-input rounded-lg px-3 py-2 text-sm bg-background w-24"
            />
          </div>
          <FileUpload onTextLoaded={(text) => startSession(text)} />
        </div>
      ) : (
        <div className="grid grid-cols-[1fr_300px] gap-6">
          {/* Main content */}
          <div className="space-y-6">
            {analysis.loading && (
              <ProgressStream
                message={analysis.progress}
                detail={analysis.progressDetail}
                completedSteps={completedSteps}
                totalSteps={totalSteps}
                startedAt={startedAtRef.current}
                onCancel={analysis.cancel}
              />
            )}

            {analysis.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
                {analysis.error}
              </div>
            )}

            {isReady && !analysis.loading && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <p className="text-sm text-green-800 font-medium">
                  Artifact meets the target score of {threshold}!
                </p>
              </div>
            )}

            {editMode ? (
              <div className="space-y-3">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full h-96 p-3 border border-input rounded-lg bg-background text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
                  >
                    Save & Re-analyse
                  </button>
                  <button
                    onClick={() => setEditMode(false)}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                {result && !analysis.loading && (
                  <div className="flex gap-2 mb-4">
                    <button
                      onClick={() => { setEditText(artifactText); setEditMode(true) }}
                      className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium"
                    >
                      Edit Artifact
                    </button>
                    <button
                      onClick={() => runAnalysis()}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
                    >
                      Re-analyse
                    </button>
                  </div>
                )}

                {result && (
                  <AnalysisReport
                    result={result.result}
                    onSuggestionAction={handleApplySuggestions}
                  />
                )}
              </>
            )}

            {applying && (
              <ProgressStream
                message="Applying suggestions..."
                startedAt={Date.now()}
              />
            )}
          </div>

          {/* Sidebar — iteration history */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Iteration History</h3>
            <div className="space-y-2">
              {history.map((h, i) => (
                <div
                  key={h.iteration}
                  className="flex items-center justify-between bg-card border border-border rounded-lg px-3 py-2"
                >
                  <span className="text-sm">#{h.iteration}</span>
                  <span className={cn(
                    "text-sm font-bold",
                    h.score >= 70 ? "text-green-600" : h.score >= 40 ? "text-amber-500" : "text-red-500",
                  )}>
                    {Math.round(h.score)}
                  </span>
                  {i > 0 && (
                    <span className={cn("text-xs", h.score > history[i - 1].score ? "text-green-600" : "text-red-500")}>
                      {h.score > history[i - 1].score ? (
                        <ArrowUp className="h-3 w-3 inline" />
                      ) : (
                        <ArrowDown className="h-3 w-3 inline" />
                      )}
                      {Math.abs(Math.round(h.score - history[i - 1].score))}
                    </span>
                  )}
                </div>
              ))}
            </div>

            {comparison && (
              <div className="border border-border rounded-lg p-3 space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground">Latest Changes</h4>
                {comparison.improved_dimensions.length > 0 && (
                  <div>
                    <p className="text-xs text-green-600 font-medium">Improved:</p>
                    {comparison.improved_dimensions.map((d) => (
                      <p key={d} className="text-xs text-muted-foreground pl-2">{d}</p>
                    ))}
                  </div>
                )}
                {comparison.resolved_issues.length > 0 && (
                  <p className="text-xs text-green-600">
                    {comparison.resolved_issues.length} issues resolved
                  </p>
                )}
                {comparison.new_issues.length > 0 && (
                  <p className="text-xs text-red-500">
                    {comparison.new_issues.length} new issues
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
