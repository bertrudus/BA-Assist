import type { UserStory } from "@/api/types"
import { cn } from "@/lib/utils"

const priorityColors: Record<string, string> = {
  Must: "bg-red-100 text-red-800",
  Should: "bg-amber-100 text-amber-800",
  Could: "bg-blue-100 text-blue-800",
  "Won't": "bg-gray-100 text-gray-600",
}

const complexityColors: Record<string, string> = {
  S: "bg-green-100 text-green-800",
  M: "bg-blue-100 text-blue-800",
  L: "bg-amber-100 text-amber-800",
  XL: "bg-red-100 text-red-800",
}

export function StoryCard({ story }: { story: UserStory }) {
  return (
    <div className="border border-border rounded-lg p-4 bg-card hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-semibold">{story.id}: {story.title}</h4>
        <div className="flex gap-1 shrink-0">
          <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", priorityColors[story.priority])}>
            {story.priority}
          </span>
          <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", complexityColors[story.estimate_complexity])}>
            {story.estimate_complexity}
          </span>
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-3">
        <span className="font-medium">As a</span> {story.persona},{" "}
        <span className="font-medium">I want</span> {story.goal},{" "}
        <span className="font-medium">so that</span> {story.benefit}.
      </p>

      {story.acceptance_criteria.length > 0 && (
        <details className="group">
          <summary className="text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground">
            Acceptance Criteria ({story.acceptance_criteria.length})
          </summary>
          <ul className="mt-2 space-y-1 pl-4">
            {story.acceptance_criteria.map((ac, i) => (
              <li key={i} className="text-xs text-muted-foreground list-disc">
                {ac}
              </li>
            ))}
          </ul>
        </details>
      )}

      {story.dependencies.length > 0 && (
        <p className="text-xs text-muted-foreground mt-2">
          Dependencies: {story.dependencies.join(", ")}
        </p>
      )}
    </div>
  )
}
