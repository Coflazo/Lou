import { AnimatePresence, motion } from "framer-motion";
import { X } from "@phosphor-icons/react";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, subtitle, children, className }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
      previouslyFocused?.focus?.();
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-[color:var(--surface-overlay)]"
            aria-hidden
          />
          <motion.div
            ref={panelRef}
            tabIndex={-1}
            role="dialog"
            aria-modal
            aria-labelledby={title ? "modal-title" : undefined}
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 280, damping: 26 }}
            className={cn(
              "fixed inset-x-4 top-[10vh] z-50 mx-auto max-w-2xl bg-surface-raised rounded-[18px] shadow-[var(--shadow-4)] p-6 outline-none",
              className,
            )}
          >
            <header className="flex items-start justify-between gap-4 mb-4">
              {title && (
                <div className="flex flex-col gap-1">
                  <h2 id="modal-title" className="text-2xl">
                    {title}
                  </h2>
                  {subtitle && <p className="text-[color:var(--color-warm-gray)] text-base">{subtitle}</p>}
                </div>
              )}
              <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-[8px] hover:bg-surface-sunken">
                <X size={16} />
              </button>
            </header>
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
