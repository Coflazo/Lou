import { AnimatePresence, motion } from "framer-motion";
import { Outlet } from "react-router-dom";
import { useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useUiStore } from "@/stores/uiStore";

export function Shell() {
  const toast = useUiStore((state) => state.toast);
  const dismissToast = useUiStore((state) => state.dismissToast);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(dismissToast, 4200);
    return () => window.clearTimeout(id);
  }, [toast, dismissToast]);

  return (
    <div className="grid min-h-screen [grid-template-columns:240px_1fr] [grid-template-rows:56px_1fr] bg-surface-base">
      <Sidebar />
      <TopBar />
      <main className="col-start-2 col-end-3 row-start-2 row-end-3 overflow-auto px-8 py-8">
        <Outlet />
      </main>

      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="fixed bottom-6 right-6 z-50 max-w-sm px-4 py-3 rounded-[12px] bg-ink text-paper shadow-[var(--shadow-3)] flex items-center gap-3"
          >
            <span className="eyebrow text-[color:var(--color-amber)]">Lou</span>
            <span className="text-base">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
