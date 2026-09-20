import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { ToastProvider } from "./components/ui/Toast";
import { AnalyzePage } from "./pages/AnalyzePage";
import { DashboardPage } from "./pages/DashboardPage";
import { UploadPage } from "./pages/UploadPage";
import { WorkspacePage } from "./pages/WorkspacePage";
import { FlowStageProvider } from "./state/flowStage";

// The outgoing page stays mounted (popped out of layout) while the incoming one mounts,
// which is what lets the shared glass surface morph between screens.
function AnimatedRoutes() {
  const location = useLocation();
  const screen = location.pathname.split("/")[1] || "home";

  return (
    <AnimatePresence mode="popLayout" initial={false}>
      <motion.div key={screen} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
        <Routes location={location}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/analyze/:id" element={<AnalyzePage />} />
          <Route path="/workspace/:id" element={<WorkspacePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <FlowStageProvider>
            <AppShell>
              <AnimatedRoutes />
            </AppShell>
          </FlowStageProvider>
        </BrowserRouter>
      </ToastProvider>
    </MotionConfig>
  );
}
