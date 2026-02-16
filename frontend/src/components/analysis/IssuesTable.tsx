import type { Issue } from "@/api/types"
import { SeverityBadge } from "@/components/shared/SeverityBadge"

interface IssuesTableProps {
  issues: Issue[]
}

export function IssuesTable({ issues }: IssuesTableProps) {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-2 text-left font-medium">ID</th>
            <th className="px-4 py-2 text-left font-medium">Severity</th>
            <th className="px-4 py-2 text-left font-medium">Dimension</th>
            <th className="px-4 py-2 text-left font-medium">Description</th>
            <th className="px-4 py-2 text-left font-medium">Recommendation</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {issues.map((issue) => (
            <tr key={issue.id} className="hover:bg-muted/50">
              <td className="px-4 py-3 font-mono text-xs">{issue.id}</td>
              <td className="px-4 py-3">
                <SeverityBadge severity={issue.severity} />
              </td>
              <td className="px-4 py-3">{issue.dimension}</td>
              <td className="px-4 py-3">
                <p>{issue.description}</p>
                {issue.location && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Location: {issue.location}
                  </p>
                )}
              </td>
              <td className="px-4 py-3 text-muted-foreground">{issue.recommendation}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
