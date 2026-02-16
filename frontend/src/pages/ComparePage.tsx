import { useState } from "react"
import { FileUpload } from "@/components/shared/FileUpload"
import { ProgressStream } from "@/components/shared/ProgressStream"
import { CompareView } from "@/components/compare/CompareView"
import { useSSE } from "@/hooks/useSSE"
import type { AnalysisResult, ComparisonReport } from "@/api/types"

interface CompareResult {
  result_1: AnalysisResult
  result_2: AnalysisResult
  comparison: ComparisonReport
}

export function ComparePage() {
  const [text1, setText1] = useState("")
  const [_text2, setText2] = useState("")
  const [step, setStep] = useState<1 | 2 | "running" | "done">(1)
  const comparison = useSSE<CompareResult>()

  const handleFile1 = (text: string) => {
    setText1(text)
    setStep(2)
  }

  const handleFile2 = (text: string) => {
    setText2(text)
    setStep("running")
    comparison.start("/api/compare", {
      artifact_text_1: text1,
      artifact_text_2: text,
    })
  }

  if (comparison.result && step !== "done") {
    setStep("done")
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compare Artifacts</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Compare two versions of an artifact side-by-side.
        </p>
      </div>

      {step === 1 && (
        <div>
          <h3 className="text-sm font-medium mb-3">Upload first artifact</h3>
          <FileUpload onTextLoaded={handleFile1} />
        </div>
      )}

      {step === 2 && (
        <div>
          <div className="bg-muted rounded-lg px-4 py-3 mb-4">
            <p className="text-sm font-medium">Artifact 1 loaded ({text1.length.toLocaleString()} chars)</p>
          </div>
          <h3 className="text-sm font-medium mb-3">Upload second artifact</h3>
          <FileUpload onTextLoaded={handleFile2} />
        </div>
      )}

      {comparison.loading && (
        <ProgressStream message={comparison.progress} detail={comparison.progressDetail} />
      )}

      {comparison.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          {comparison.error}
        </div>
      )}

      {comparison.result && (
        <>
          <button
            onClick={() => { setText1(""); setText2(""); setStep(1) }}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            New comparison
          </button>
          <CompareView
            result1={comparison.result.result_1}
            result2={comparison.result.result_2}
            comparison={comparison.result.comparison}
          />
        </>
      )}
    </div>
  )
}
