import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { AnalysePage } from "@/pages/AnalysePage"
import { IteratePage } from "@/pages/IteratePage"
import { StoriesPage } from "@/pages/StoriesPage"
import { ComparePage } from "@/pages/ComparePage"
import { ExportPage } from "@/pages/ExportPage"
import { ConfigPage } from "@/pages/ConfigPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/analyse" replace />} />
          <Route path="/analyse" element={<AnalysePage />} />
          <Route path="/iterate" element={<IteratePage />} />
          <Route path="/stories" element={<StoriesPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/export" element={<ExportPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
