import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  eyebrow?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, eyebrow, subtitle, actions, className }: PageHeaderProps) {
  return (
    <header className={cn("flex flex-wrap items-end justify-between gap-4 mb-8", className)}>
      <div className="flex flex-col gap-2 max-w-xl">
        {eyebrow && (
          <motion.span
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.32 }}
            className="eyebrow"
          >
            {eyebrow}
          </motion.span>
        )}
        <motion.h1
          initial={{ clipPath: "inset(0 100% 0 0)", opacity: 0 }}
          animate={{ clipPath: "inset(0 0% 0 0)", opacity: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-3xl text-ink"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08, duration: 0.4 }}
            className="text-[color:var(--color-warm-gray)] text-md"
          >
            {subtitle}
          </motion.p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
