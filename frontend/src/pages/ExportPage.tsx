import { useState } from "react"
import { FileUpload } from "@/components/shared/FileUpload"
import { ProgressStream } from "@/components/shared/ProgressStream"
import { useSSE } from "@/hooks/useSSE"
import { api } from "@/api/client"
import type { UserStory, CoverageReport } from "@/api/types"
import { Download, FileText, Braces, Table, FolderCode } from "lucide-react"

interface StoriesResult {
  stories: UserStory[]
  coverage: CoverageReport
}

export function ExportPage() {
  const [artifactText, setArtifactText] = useState("")
  const generation = useSSE<StoriesResult>()

  const handleGenerate = (text: string) => {
    setArtifactText(text)
    generation.start("/api/stories/generate", { artifact_text: text })
  }

  const stories = generation.result?.stories || []

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

  const exportFormats = [
    { format: "markdown", label: "Markdown", desc: "Human-readable story cards (.md)", icon: FileText },
    { format: "json", label: "JSON", desc: "Structured data for tool integration (.json)", icon: Braces },
    { format: "csv", label: "CSV", desc: "Import into Jira / Azure DevOps / Trello (.csv)", icon: Table },
    { format: "claude-code", label: "Claude Code Scaffold", desc: "Full project scaffold with CLAUDE.md, backlog, architecture (.zip)", icon: FolderCode },
  ]

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Export</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate stories from requirements, then export in your preferred format.
        </p>
      </div>

      {!artifactText ? (
        <FileUpload onTextLoaded={(text) => handleGenerate(text)} />
      ) : (
        <>
          {generation.loading && (
            <ProgressStream message={generation.progress} detail={generation.progressDetail} />
          )}

          {generation.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
              {generation.error}
            </div>
          )}

          {stories.length > 0 && (
            <div className="space-y-4">
              <div className="bg-muted rounded-lg px-4 py-3">
                <p className="text-sm font-medium">
                  {stories.length} stories ready to export
                </p>
                <button
                  onClick={() => setArtifactText("")}
                  className="text-xs text-muted-foreground hover:text-foreground underline mt-1"
                >
                  Start over
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {exportFormats.map(({ format, label, desc, icon: Icon }) => (
                  <button
                    key={format}
                    onClick={() => handleExport(format)}
                    className="flex items-start gap-4 border border-border rounded-lg p-5 hover:bg-muted hover:border-primary/30 transition-colors text-left group"
                  >
                    <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold">{label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{desc}</p>
                    </div>
                    <Download className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
