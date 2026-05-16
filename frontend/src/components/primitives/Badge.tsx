import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "low" | "medium" | "high" | "accent" | "success";

interface BadgeProps {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}

const TONE_STYLES: Record<Tone, string> = {
  neutral: "bg-surface-sunken text-[color:var(--color-ink-soft)]",
  low: "bg-[color:var(--color-green-soft)] text-[color:var(--color-green)]",
  medium: "bg-[color:var(--color-amber-soft)] text-[color:var(--color-ink)]",
  high: "bg-[color:var(--color-red-soft)] text-[color:var(--color-red)]",
  accent: "bg-[color:var(--color-amber)] text-[color:var(--color-ink)]",
  success: "bg-[color:var(--color-green)] text-paper",
};

export function Badge({ tone = "neutral", children, className }: BadgeProps) {
  return (
    <motion.span
      initial={{ clipPath: "inset(0 100% 0 0)", opacity: 0 }}
      animate={{ clipPath: "inset(0 0% 0 0)", opacity: 1 }}
      transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono uppercase tracking-wider rounded-[6px]",
        TONE_STYLES[tone],
        className,
      )}
    >
      {children}
    </motion.span>
  );
}
