import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { ImageGenPage } from "@/pages/ImageGenPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/:projectId" element={<ProjectDetail />} />
        <Route path="/image-gen" element={<ImageGenPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
