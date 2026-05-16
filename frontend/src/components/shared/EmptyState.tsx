import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  body?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ title, body, icon, action, className }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "flex flex-col items-center justify-center text-center gap-3 py-12 px-8 rounded-[16px] bg-surface-raised border border-dashed border-[color:var(--border-soft)]",
        className,
      )}
    >
      {icon && <div className="text-[color:var(--color-warm-gray)]">{icon}</div>}
      <h3 className="text-xl text-ink">{title}</h3>
      {body && <p className="text-[color:var(--color-warm-gray)] max-w-md text-base">{body}</p>}
      {action}
    </motion.div>
  );
}
