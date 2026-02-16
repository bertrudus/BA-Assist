import { useCallback, useState, type DragEvent } from "react"
import { Upload } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/api/client"

interface FileUploadProps {
  onTextLoaded: (text: string, filename?: string) => void
  accept?: string
  className?: string
}

export function FileUpload({ onTextLoaded, accept = ".md,.txt,.doc", className }: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [pasteMode, setPasteMode] = useState(false)
  const [pasteText, setPasteText] = useState("")

  const handleFile = useCallback(
    async (file: File) => {
      const result = await api.uploadFile(file)
      onTextLoaded(result.text, result.filename)
    },
    [onTextLoaded],
  )

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [handleFile],
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleFile(file)
    },
    [handleFile],
  )

  if (pasteMode) {
    return (
      <div className={cn("space-y-3", className)}>
        <textarea
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
          placeholder="Paste your artifact text here..."
          className="w-full h-64 p-3 border border-input rounded-lg bg-background text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (pasteText.trim()) onTextLoaded(pasteText.trim())
            }}
            disabled={!pasteText.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            Load Text
          </button>
          <button
            onClick={() => setPasteMode(false)}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm"
          >
            Back to Upload
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-8 transition-colors cursor-pointer",
          dragOver
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50",
        )}
      >
        <Upload className="h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm font-medium">Drop a file here or click to upload</p>
        <p className="text-xs text-muted-foreground mt-1">
          Supports .md, .txt files
        </p>
        <input
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="absolute inset-0 opacity-0 cursor-pointer"
        />
      </div>
      <button
        onClick={() => setPasteMode(true)}
        className="text-sm text-muted-foreground hover:text-foreground underline"
      >
        Or paste text directly
      </button>
    </div>
  )
}
