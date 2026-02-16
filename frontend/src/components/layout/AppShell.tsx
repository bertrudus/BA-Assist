import { NavLink, Outlet } from "react-router-dom"
import {
  FileSearch,
  RefreshCw,
  BookOpen,
  GitCompare,
  Download,
  Settings,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/analyse", label: "Analyse", icon: FileSearch },
  { to: "/iterate", label: "Iterate", icon: RefreshCw },
  { to: "/stories", label: "Stories", icon: BookOpen },
  { to: "/compare", label: "Compare", icon: GitCompare },
  { to: "/export", label: "Export", icon: Download },
  { to: "/config", label: "Config", icon: Settings },
]

export function AppShell() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-border bg-sidebar-background flex flex-col">
        <div className="p-4 border-b border-border">
          <h1 className="text-lg font-bold text-sidebar-foreground">
            BA Analyser
          </h1>
          <p className="text-xs text-muted-foreground">Artifact Analysis Tool</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-border text-xs text-muted-foreground">
          v0.1.0
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
