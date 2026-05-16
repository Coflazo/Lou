import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Shell } from "@/components/layout";
import { RoleGate } from "@/components/shared/RoleGate";
import { LoginPage } from "@/pages/Login";
import { DashboardPage } from "@/pages/Dashboard";
import { PlaybookListPage } from "@/pages/Playbooks/PlaybookList";
import { PlaybookDetailPage } from "@/pages/Playbooks/PlaybookDetail";
import { ContractListPage } from "@/pages/Contracts/ContractList";
import { ContractUploadPage } from "@/pages/Contracts/ContractUpload";
import { ContractAnalysisPage } from "@/pages/Contracts/ContractAnalysis";
import { ReviewQueuePage } from "@/pages/Review/ReviewQueue";
import { VoiceSessionPage } from "@/pages/Voice/VoiceSession";
import { CompanyBrainPage } from "@/pages/Brain/CompanyBrain";
import { ExportPanelPage } from "@/pages/Export/ExportPanel";

function PageTransition({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<Shell />}>
        <Route path="/dashboard" element={<PageTransition><DashboardPage /></PageTransition>} />
        <Route path="/playbooks" element={<PageTransition><PlaybookListPage /></PageTransition>} />
        <Route path="/playbooks/:id" element={<PageTransition><PlaybookDetailPage /></PageTransition>} />
        <Route path="/contracts" element={<PageTransition><ContractListPage /></PageTransition>} />
        <Route path="/contracts/new" element={<PageTransition><ContractUploadPage /></PageTransition>} />
        <Route path="/contracts/:id" element={<PageTransition><ContractAnalysisPage /></PageTransition>} />
        <Route
          path="/review"
          element={
            <PageTransition>
              <RoleGate required="SENIOR">
                <ReviewQueuePage />
              </RoleGate>
            </PageTransition>
          }
        />
        <Route path="/voice" element={<PageTransition><VoiceSessionPage /></PageTransition>} />
        <Route
          path="/brain"
          element={
            <PageTransition>
              <RoleGate required="ADMIN">
                <CompanyBrainPage />
              </RoleGate>
            </PageTransition>
          }
        />
        <Route
          path="/exports"
          element={
            <PageTransition>
              <RoleGate required="SENIOR">
                <ExportPanelPage />
              </RoleGate>
            </PageTransition>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
