import { useCallback, useRef, useState } from "react"
import { connectSSE } from "@/api/sse"
import type { SSEEvent } from "@/api/types"

interface SSEState<T> {
  loading: boolean
  progress: string
  progressDetail: Record<string, unknown> | null
  result: T | null
  error: string | null
}

export function useSSE<T>() {
  const [state, setState] = useState<SSEState<T>>({
    loading: false,
    progress: "",
    progressDetail: null,
    result: null,
    error: null,
  })
  const controllerRef = useRef<AbortController | null>(null)

  const start = useCallback(
    (
      url: string,
      body: unknown,
      options?: {
        onProgress?: (event: SSEEvent) => void
        extractResult?: (event: SSEEvent) => T
      },
    ) => {
      // Cancel any existing request
      controllerRef.current?.abort()

      setState({
        loading: true,
        progress: "Starting...",
        progressDetail: null,
        result: null,
        error: null,
      })

      const controller = connectSSE(
        url,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
        (event) => {
          if (event.event === "progress") {
            setState((prev) => ({
              ...prev,
              progress: (event.data.message as string) || "",
              progressDetail: event.data,
            }))
            options?.onProgress?.(event)
          } else if (event.event === "dimension_complete" || event.event === "step_complete" || event.event === "artifact_complete") {
            options?.onProgress?.(event)
          } else if (event.event === "complete") {
            const result = options?.extractResult
              ? options.extractResult(event)
              : (event.data as unknown as T)
            setState({
              loading: false,
              progress: "",
              progressDetail: null,
              result,
              error: null,
            })
          }
        },
        (error) => {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: error.message,
          }))
        },
      )

      controllerRef.current = controller
    },
    [],
  )

  const cancel = useCallback(() => {
    controllerRef.current?.abort()
    setState((prev) => ({ ...prev, loading: false, progress: "" }))
  }, [])

  return { ...state, start, cancel }
}
