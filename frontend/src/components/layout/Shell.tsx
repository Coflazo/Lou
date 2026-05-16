import { AnimatePresence, motion } from "framer-motion";
import { Outlet } from "react-router-dom";
import { useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useUiStore } from "@/stores/uiStore";
import { SIDEBAR_DRAWER_WIDTH_PX, SIDEBAR_WIDTH_PX, TOAST_DURATION_MS } from "@/lib/constants";

export function Shell() {
  const toast = useUiStore((state) => state.toast);
  const dismissToast = useUiStore((state) => state.dismissToast);
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(dismissToast, TOAST_DURATION_MS);
    return () => window.clearTimeout(id);
  }, [toast, dismissToast]);

  useEffect(() => {
    if (!sidebarOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sidebarOpen, setSidebarOpen]);

  return (
    <div
      className="grid min-h-screen grid-cols-1 md:[grid-template-columns:var(--lou-sidebar)_1fr] [grid-template-rows:56px_1fr] bg-surface-base"
      style={{ ["--lou-sidebar" as string]: `${SIDEBAR_WIDTH_PX}px` }}
    >
      <Sidebar drawerWidth={SIDEBAR_DRAWER_WIDTH_PX} />
      <TopBar />
      <main className="col-start-1 col-end-2 md:col-start-2 md:col-end-3 row-start-2 row-end-3 overflow-auto px-4 py-4 md:px-8 md:py-8">
        <Outlet />
      </main>

      <AnimatePresence>
        {sidebarOpen && (
          <motion.button
            key="scrim"
            type="button"
            aria-label="Close navigation"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setSidebarOpen(false)}
            className="md:hidden fixed inset-0 z-40 bg-ink"
          />
        )}
      </AnimatePresence>

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
