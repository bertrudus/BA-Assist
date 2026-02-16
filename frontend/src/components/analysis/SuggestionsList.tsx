import { useState } from "react"
import type { Suggestion } from "@/api/types"
import { cn } from "@/lib/utils"

interface SuggestionsListProps {
  suggestions: Suggestion[]
  onApply?: (ids: string[]) => void
}

export function SuggestionsList({ suggestions, onApply }: SuggestionsListProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    setSelected(new Set(suggestions.map((s) => s.id)))
  }

  return (
    <div className="space-y-3">
      {onApply && (
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-lg text-xs font-medium hover:opacity-80"
          >
            Select All
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-lg text-xs font-medium hover:opacity-80"
          >
            Clear
          </button>
          <button
            onClick={() => onApply(Array.from(selected))}
            disabled={selected.size === 0}
            className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:opacity-90 disabled:opacity-50"
          >
            Apply Selected ({selected.size})
          </button>
        </div>
      )}

      {suggestions.map((sug) => (
        <div
          key={sug.id}
          className={cn(
            "border rounded-lg p-4 transition-colors",
            onApply ? "cursor-pointer" : "",
            selected.has(sug.id) ? "border-primary bg-primary/5" : "border-border",
          )}
          onClick={() => onApply && toggle(sug.id)}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-xs text-muted-foreground">{sug.id}</span>
            {onApply && (
              <input
                type="checkbox"
                checked={selected.has(sug.id)}
                onChange={() => toggle(sug.id)}
                className="h-4 w-4"
                onClick={(e) => e.stopPropagation()}
              />
            )}
          </div>
          <p className="text-sm mb-2">{sug.rationale}</p>
          <div className="font-mono text-xs space-y-1 bg-muted rounded-md p-3">
            <div className="text-red-600">- {sug.original_text}</div>
            <div className="text-green-600">+ {sug.suggested_text}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
