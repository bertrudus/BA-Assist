import { useCallback, useRef, useState } from "react"
import { FileUpload } from "@/components/shared/FileUpload"
import { ProgressStream, type CompletedStep } from "@/components/shared/ProgressStream"
import { AnalysisReport } from "@/components/analysis/AnalysisReport"
import { useSSE } from "@/hooks/useSSE"
import type { AnalysisResult, ArtifactType, SSEEvent } from "@/api/types"

export function AnalysePage() {
  const [artifactText, setArtifactText] = useState("")
  const [filename, setFilename] = useState("")
  const [artifactType, setArtifactType] = useState<ArtifactType | "">("")
  const [completedSteps, setCompletedSteps] = useState<CompletedStep[]>([])
  const [totalSteps, setTotalSteps] = useState<number | undefined>()
  const startedAtRef = useRef<number>(0)
  const analysis = useSSE<AnalysisResult>()

  const handleTextLoaded = (text: string, name?: string) => {
    setArtifactText(text)
    setFilename(name || "pasted text")
  }

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
    if (event.event === "type_detected") {
      setCompletedSteps((prev) => [
        ...prev,
        { name: `Detected: ${(event.data.artifact_type as string).replace(/_/g, " ")}`, completedAt: Date.now() },
      ])
    }
  }, [])

  const handleAnalyse = () => {
    setCompletedSteps([])
    setTotalSteps(undefined)
    startedAtRef.current = Date.now()
    analysis.start("/api/analyse", {
      artifact_text: artifactText,
      artifact_type: artifactType || null,
      threshold: 80,
    }, {
      onProgress: handleProgress,
    })
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analyse Artifact</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload or paste a BA artifact to analyse its quality.
        </p>
      </div>

      {!artifactText ? (
        <FileUpload onTextLoaded={handleTextLoaded} />
      ) : (
        <div className="space-y-4">
          {/* Loaded file info */}
          <div className="flex items-center justify-between bg-muted rounded-lg px-4 py-3">
            <div>
              <p className="text-sm font-medium">{filename}</p>
              <p className="text-xs text-muted-foreground">{artifactText.length.toLocaleString()} characters</p>
            </div>
            <button
              onClick={() => { setArtifactText(""); setFilename("") }}
              disabled={analysis.loading}
              className="text-xs text-muted-foreground hover:text-foreground underline disabled:opacity-50"
            >
              Change file
            </button>
          </div>

          {/* Options */}
          <div className="flex items-end gap-4">
            <div>
              <label className="text-sm font-medium block mb-1">Artifact Type</label>
              <select
                value={artifactType}
                onChange={(e) => setArtifactType(e.target.value as ArtifactType)}
                disabled={analysis.loading}
                className="border border-input rounded-lg px-3 py-2 text-sm bg-background disabled:opacity-50"
              >
                <option value="">Auto-detect</option>
                <option value="requirements_document">Requirements Document</option>
                <option value="business_process">Business Process</option>
                <option value="user_story">User Story</option>
                <option value="use_case">Use Case</option>
              </select>
            </div>
            <button
              onClick={handleAnalyse}
              disabled={analysis.loading}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
            >
              {analysis.loading ? "Analysing..." : "Analyse"}
            </button>
          </div>
        </div>
      )}

      {/* Progress */}
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

      {/* Error */}
      {analysis.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          {analysis.error}
        </div>
      )}

      {/* Results */}
      {analysis.result && <AnalysisReport result={analysis.result} />}
    </div>
  )
}
