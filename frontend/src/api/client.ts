const BASE = ""

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  getConfig: () => request<Record<string, unknown>>("/api/config"),

  uploadFile: async (file: File): Promise<{ filename: string; text: string }> => {
    const form = new FormData()
    form.append("file", file)
    const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    return res.json()
  },

  detectType: (text: string) =>
    request<{ artifact_type: string }>("/api/detect-type", {
      method: "POST",
      body: JSON.stringify({ artifact_text: text }),
    }),

  listSessions: () => request<Record<string, unknown>[]>("/api/sessions"),

  createSession: (text: string, threshold = 80) =>
    request<{ id: string }>("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ artifact_text: text, threshold }),
    }),

  getSession: (id: string) => request<Record<string, unknown>>(`/api/sessions/${id}`),

  deleteSession: (id: string) =>
    request<{ deleted: boolean }>(`/api/sessions/${id}`, { method: "DELETE" }),

  getSuggestions: (id: string) =>
    request<Record<string, unknown>[]>(`/api/sessions/${id}/suggestions`),

  applySuggestions: (id: string, ids: string[]) =>
    request<{ artifact_text: string }>(`/api/sessions/${id}/apply-suggestions`, {
      method: "POST",
      body: JSON.stringify({ accepted_suggestion_ids: ids }),
    }),

  updateArtifact: (id: string, text: string) =>
    request<{ artifact_text: string }>(`/api/sessions/${id}/artifact`, {
      method: "PUT",
      body: JSON.stringify({ artifact_text: text }),
    }),

  exportFile: async (
    format: string,
    stories: Record<string, unknown>[],
    artifactText?: string,
  ): Promise<Blob> => {
    const body: Record<string, unknown> = { stories }
    if (artifactText) body.artifact_text = artifactText
    const res = await fetch(`${BASE}/api/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Export failed: ${res.status}`)
    return res.blob()
  },
}
