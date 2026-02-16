import { useCallback, useMemo, useRef, useState } from "react"
import { FileUpload } from "@/components/shared/FileUpload"
import { ProgressStream, type CompletedStep } from "@/components/shared/ProgressStream"
import { EpicGroup } from "@/components/stories/EpicGroup"
import { ScoreGauge } from "@/components/shared/ScoreGauge"
import { useSSE } from "@/hooks/useSSE"
import { api } from "@/api/client"
import type { UserStory, CoverageReport, SSEEvent } from "@/api/types"
import { Download } from "lucide-react"

interface StoriesResult {
  stories: UserStory[]
  coverage: CoverageReport
}

const STEP_LABELS: Record<string, string> = {
  extracting_requirements: "Extract requirements",
  identifying_personas: "Identify personas",
  generating_stories: "Generate stories",
  validating_coverage: "Validate coverage",
}

export function StoriesPage() {
  const [artifactText, setArtifactText] = useState("")
  const [activeTab, setActiveTab] = useState<"stories" | "coverage" | "export">("stories")
  const [completedSteps, setCompletedSteps] = useState<CompletedStep[]>([])
  const startedAtRef = useRef<number>(0)
  const generation = useSSE<StoriesResult>()

  const handleProgress = useCallback((event: SSEEvent) => {
    if (event.event === "step_complete") {
      const stepKey = event.data.step as string
      const count = event.data.count as number | undefined
      setCompletedSteps((prev) => [
        ...prev,
        {
          name: STEP_LABELS[stepKey] || stepKey,
          score: count,
          completedAt: Date.now(),
        },
      ])
    }
  }, [])

  const handleGenerate = (text: string) => {
    setArtifactText(text)
    setCompletedSteps([])
    startedAtRef.current = Date.now()
    generation.start("/api/stories/generate", { artifact_text: text }, {
      onProgress: handleProgress,
    })
  }

  const stories = generation.result?.stories || []
  const coverage = generation.result?.coverage

  const epicGroups = useMemo(() => {
    const groups: Record<string, UserStory[]> = {}
    for (const story of stories) {
      ;(groups[story.epic] ??= []).push(story)
    }
    return groups
  }, [stories])

  const handleExport = async (format: string) => {
    const blob = await api.exportFile(
      format,
      stories as unknown as Record<string, unknown>[],
      artifactText,
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    const ext = format === "claude-code" ? "zip" : format === "json" ? "json" : format === "csv" ? "csv" : "md"
    a.download = `user-stories.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Generate Stories</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Convert requirements into development-ready user stories.
        </p>
      </div>

      {!artifactText ? (
        <FileUpload onTextLoaded={(text) => handleGenerate(text)} />
      ) : (
        <>
          {generation.loading && (
            <ProgressStream
              message={generation.progress}
              detail={generation.progressDetail}
              completedSteps={completedSteps}
              totalSteps={4}
              startedAt={startedAtRef.current}
              onCancel={generation.cancel}
            />
          )}

          {generation.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
              {generation.error}
            </div>
          )}

          {stories.length > 0 && (
            <>
              {/* Summary bar */}
              <div className="flex items-center justify-between bg-muted rounded-lg px-4 py-3">
                <p className="text-sm font-medium">
                  {stories.length} stories in {Object.keys(epicGroups).length} epics
                </p>
                <button
                  onClick={() => { setArtifactText("") }}
                  className="text-xs text-muted-foreground hover:text-foreground underline"
                >
                  New generation
                </button>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 border-b border-border">
                {(["stories", "coverage", "export"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab
                        ? "border-primary text-foreground"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {activeTab === "stories" && (
                <div className="space-y-6">
                  {Object.entries(epicGroups).map(([epic, epicStories]) => (
                    <EpicGroup key={epic} epic={epic} stories={epicStories} />
                  ))}
                </div>
              )}

              {activeTab === "coverage" && coverage && (
                <div className="space-y-6">
                  <div className="flex items-center gap-6">
                    <ScoreGauge score={coverage.coverage_percentage} size="lg" label="Coverage" />
                    <div>
                      <p className="text-sm">
                        <span className="font-bold">{coverage.covered_requirements}</span> of{" "}
                        <span className="font-bold">{coverage.total_requirements}</span> requirements covered
                      </p>
                    </div>
                  </div>
                  {coverage.uncovered_requirements.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-red-600 mb-2">Uncovered Requirements</h4>
                      <ul className="space-y-1">
                        {coverage.uncovered_requirements.map((r) => (
                          <li key={r} className="text-sm text-muted-foreground">{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "export" && (
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { format: "markdown", label: "Markdown", desc: "Human-readable story cards" },
                    { format: "json", label: "JSON", desc: "Structured data for tool integration" },
                    { format: "csv", label: "CSV", desc: "Import into Jira / Azure DevOps" },
                    { format: "claude-code", label: "Claude Code", desc: "Project scaffold with CLAUDE.md" },
                  ].map(({ format, label, desc }) => (
                    <button
                      key={format}
                      onClick={() => handleExport(format)}
                      className="flex items-center gap-3 border border-border rounded-lg p-4 hover:bg-muted transition-colors text-left"
                    >
                      <Download className="h-5 w-5 text-muted-foreground shrink-0" />
                      <div>
                        <p className="text-sm font-medium">{label}</p>
                        <p className="text-xs text-muted-foreground">{desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
