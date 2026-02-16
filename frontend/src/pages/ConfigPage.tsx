import { useEffect } from "react"
import { useConfigStore } from "@/stores/configStore"
import { Loader2 } from "lucide-react"

export function ConfigPage() {
  const { config, loading, error, fetchConfig } = useConfigStore()

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  if (loading && !config) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          Failed to load config: {error}
        </div>
      </div>
    )
  }

  if (!config) return null

  const rows = [
    { label: "LLM Provider", value: config.llm_provider },
    { label: "Anthropic Model", value: config.anthropic_model_id },
    { label: "Anthropic API Key", value: config.anthropic_api_key_set ? "Configured" : "Not set" },
    { label: "Bedrock Model", value: config.bedrock_model_id },
    { label: "AWS Region", value: config.aws_region },
    { label: "Max Tokens", value: String(config.bedrock_max_tokens) },
    { label: "Analysis Temperature", value: String(config.bedrock_temperature_analysis) },
    { label: "Generation Temperature", value: String(config.bedrock_temperature_generation) },
    { label: "Quality Threshold", value: String(config.analysis_quality_threshold) },
  ]

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Configuration</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Current settings loaded from environment variables and .env file.
        </p>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Setting</th>
              <th className="px-4 py-3 text-left font-medium">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map(({ label, value }) => (
              <tr key={label} className="hover:bg-muted/50">
                <td className="px-4 py-3 font-medium">{label}</td>
                <td className="px-4 py-3 font-mono text-muted-foreground">{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        To change settings, edit the <code className="bg-muted px-1 py-0.5 rounded">.env</code> file
        and restart the server.
      </p>
    </div>
  )
}
