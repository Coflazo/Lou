import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  delayMs?: number;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({ content, children, delayMs = 350, side = "top", className }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => () => {
    if (timer.current != null) window.clearTimeout(timer.current);
  }, []);

  const handleEnter = () => {
    if (timer.current != null) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setOpen(true), delayMs);
  };
  const handleLeave = () => {
    if (timer.current != null) window.clearTimeout(timer.current);
    setOpen(false);
  };

  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  } as const;

  return (
    <span className={cn("relative inline-flex", className)} onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      {children}
      <AnimatePresence>
        {open && (
          <motion.span
            role="tooltip"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.14 }}
            className={cn(
              "absolute z-40 px-2.5 py-1.5 text-xs font-mono uppercase tracking-wider rounded-[8px] bg-ink text-paper whitespace-nowrap shadow-[var(--shadow-3)]",
              positionClasses[side],
            )}
          >
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}
