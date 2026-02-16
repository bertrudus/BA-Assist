import type { SSEEvent } from "./types"

/**
 * Connect to an SSE endpoint via fetch and parse server-sent events.
 */
export function connectSSE(
  url: string,
  options: RequestInit,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
): AbortController {
  const controller = new AbortController()

  fetch(url, {
    ...options,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`HTTP ${response.status}: ${text}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const decoder = new TextDecoder()
      let buffer = ""

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        let currentEvent = ""
        let currentData = ""

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith("data: ")) {
            currentData = line.slice(6)
          } else if (line === "" && currentEvent && currentData) {
            try {
              const data = JSON.parse(currentData)
              onEvent({ event: currentEvent, data })
            } catch {
              onEvent({ event: currentEvent, data: { raw: currentData } })
            }
            currentEvent = ""
            currentData = ""
          }
        }
      }
    })
    .catch((err: Error) => {
      if (err.name !== "AbortError") {
        onError?.(err)
      }
    })

  return controller
}
