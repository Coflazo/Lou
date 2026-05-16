import { AnimatePresence, motion } from "framer-motion";
import { MagnifyingGlass } from "@phosphor-icons/react";
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
  const command = useCommand();
  const pushToast = useUiStore((state) => state.pushToast);

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
  }

  return (
    <header className="col-start-2 col-end-3 row-start-1 row-end-2 sticky top-0 z-20 h-14 bg-surface-base/85 backdrop-blur border-b border-[color:var(--border-soft)] flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <AnimatePresence mode="wait">
          <motion.div
            key={breadcrumb}
            initial={{ clipPath: "inset(0 100% 0 0)" }}
            animate={{ clipPath: "inset(0 0% 0 0)" }}
            exit={{ clipPath: "inset(0 0 0 100%)" }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-baseline gap-2"
          >
            <span className="eyebrow">Workspace</span>
            <span className="text-md text-ink">{breadcrumb}</span>
          </motion.div>
        </AnimatePresence>
      </div>

      <form onSubmit={submit} className="relative flex items-center">
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
    </header>
  );
}
