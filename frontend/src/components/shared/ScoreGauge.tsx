import { cn } from "@/lib/utils"

interface ScoreGaugeProps {
  score: number
  size?: "sm" | "md" | "lg"
  label?: string
}

function scoreColor(score: number): string {
  if (score >= 70) return "text-green-600"
  if (score >= 40) return "text-amber-500"
  return "text-red-500"
}

function scoreBg(score: number): string {
  if (score >= 70) return "bg-green-500"
  if (score >= 40) return "bg-amber-500"
  return "bg-red-500"
}

const sizes = {
  sm: { container: "w-16 h-16", text: "text-lg", ring: 50, stroke: 5 },
  md: { container: "w-24 h-24", text: "text-2xl", ring: 75, stroke: 6 },
  lg: { container: "w-32 h-32", text: "text-3xl", ring: 100, stroke: 7 },
}

export function ScoreGauge({ score, size = "md", label }: ScoreGaugeProps) {
  const s = sizes[size]
  const radius = (s.ring - s.stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={cn("relative", s.container)}>
        <svg
          viewBox={`0 0 ${s.ring} ${s.ring}`}
          className="w-full h-full -rotate-90"
        >
          <circle
            cx={s.ring / 2}
            cy={s.ring / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={s.stroke}
            className="text-muted/30"
          />
          <circle
            cx={s.ring / 2}
            cy={s.ring / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={s.stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={cn("transition-all duration-700", scoreColor(score))}
          />
        </svg>
        <span
          className={cn(
            "absolute inset-0 flex items-center justify-center font-bold",
            s.text,
            scoreColor(score),
          )}
        >
          {Math.round(score)}
        </span>
      </div>
      {label && (
        <span className="text-xs text-muted-foreground font-medium">{label}</span>
      )}
    </div>
  )
}

export function ScoreBar({ score, label }: { score: number; label: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className={cn("font-medium", scoreColor(score))}>{Math.round(score)}</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", scoreBg(score))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
