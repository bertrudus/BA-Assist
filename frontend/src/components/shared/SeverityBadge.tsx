import { cn } from "@/lib/utils"

const styles: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-800 border-red-200",
  WARNING: "bg-amber-100 text-amber-800 border-amber-200",
  INFO: "bg-blue-100 text-blue-800 border-blue-200",
}

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        styles[severity] || styles.INFO,
      )}
    >
      {severity}
    </span>
  )
}
