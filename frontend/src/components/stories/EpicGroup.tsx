import type { UserStory } from "@/api/types"
import { StoryCard } from "./StoryCard"

interface EpicGroupProps {
  epic: string
  stories: UserStory[]
}

export function EpicGroup({ epic, stories }: EpicGroupProps) {
  return (
    <div>
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-primary" />
        {epic}
        <span className="text-xs text-muted-foreground font-normal">
          ({stories.length} {stories.length === 1 ? "story" : "stories"})
        </span>
      </h3>
      <div className="grid gap-3 pl-4">
        {stories.map((story) => (
          <StoryCard key={story.id} story={story} />
        ))}
      </div>
    </div>
  )
}
