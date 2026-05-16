import { AnimatePresence, motion } from "framer-motion";
import { List as MenuIcon, MagnifyingGlass, X } from "@phosphor-icons/react";
import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useCommand } from "@/hooks/useApi";
import { useUiStore } from "@/stores/uiStore";

const ROUTE_LABELS: Record<string, string> = {
  "/dashboard": "Overview",
  "/playbooks": "Playbooks",
  "/contracts": "Contracts",
  "/review": "Review queue",
  "/voice": "Voice session",
  "/brain": "Company brain",
  "/exports": "Exports",
};

export function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const command = useCommand();
  const pushToast = useUiStore((state) => state.pushToast);
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);

  const segments = location.pathname.split("/").filter(Boolean);
  const breadcrumb = segments.length
    ? ROUTE_LABELS[`/${segments[0]}`] || segments[0]
    : "Lou";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim()) return;
    const result = await command.mutateAsync({ command: text });
    pushToast(`${result.intent}: ${result.message}`);
    if (result.intent === "approve" || result.intent === "reject") navigate("/review");
    if (result.intent === "export") navigate("/exports");
    if (result.intent === "analyze_contract") navigate("/contracts");
    setText("");
    setMobileSearchOpen(false);
  }

  return (
    <header className="col-start-1 col-end-2 md:col-start-2 md:col-end-3 row-start-1 row-end-2 sticky top-0 z-30 h-14 bg-surface-base/85 backdrop-blur border-b border-[color:var(--border-soft)] flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label={sidebarOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={sidebarOpen}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="md:hidden inline-flex items-center justify-center min-h-11 min-w-11 rounded-[10px] hover:bg-surface-sunken transition-colors"
        >
          {sidebarOpen ? <X size={20} /> : <MenuIcon size={20} />}
        </button>
        <AnimatePresence mode="wait">
          <motion.div
            key={breadcrumb}
            initial={{ clipPath: "inset(0 100% 0 0)" }}
            animate={{ clipPath: "inset(0 0% 0 0)" }}
            exit={{ clipPath: "inset(0 0 0 100%)" }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-baseline gap-2"
          >
            <span className="eyebrow hidden sm:inline">Workspace</span>
            <span className="text-md text-ink">{breadcrumb}</span>
          </motion.div>
        </AnimatePresence>
      </div>

      <form onSubmit={submit} className="relative hidden md:flex items-center">
        <motion.div
          animate={{ width: focused ? 360 : 220 }}
          transition={{ type: "spring", stiffness: 220, damping: 24 }}
          className="flex items-center gap-2 px-3 h-9 bg-surface-sunken rounded-[10px] border border-[color:var(--border-soft)] focus-within:border-[color:var(--color-amber)] transition-colors"
        >
          <MagnifyingGlass size={14} className="text-[color:var(--color-warm-gray)]" />
          <input
            value={text}
            onChange={(event) => setText(event.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Ask Lou to review, approve, export…"
            className="flex-1 bg-transparent outline-none text-base"
          />
          {command.isPending && <span className="font-mono text-xs text-[color:var(--color-warm-gray)]">…</span>}
        </motion.div>
      </form>

      <button
        type="button"
        aria-label="Open command bar"
        onClick={() => setMobileSearchOpen(true)}
        className="md:hidden inline-flex items-center justify-center min-h-11 min-w-11 rounded-[10px] hover:bg-surface-sunken transition-colors"
      >
        <MagnifyingGlass size={20} />
      </button>

      <AnimatePresence>
        {mobileSearchOpen && (
          <motion.div
            key="cmd-sheet"
            initial={{ y: "-100%", opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "-100%", opacity: 0 }}
            transition={{ type: "spring", stiffness: 280, damping: 26 }}
            className="md:hidden absolute inset-x-0 top-full z-40 bg-surface-raised border-b border-[color:var(--border-soft)] p-4 shadow-[var(--shadow-3)]"
          >
            <form onSubmit={submit} className="flex items-center gap-2">
              <MagnifyingGlass size={16} className="text-[color:var(--color-warm-gray)]" />
              <input
                autoFocus
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Ask Lou…"
                className="flex-1 bg-transparent outline-none text-base h-10"
              />
              <button
                type="button"
                onClick={() => setMobileSearchOpen(false)}
                className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)] px-3 h-10 rounded-[8px] hover:bg-surface-sunken"
              >
                Close
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
