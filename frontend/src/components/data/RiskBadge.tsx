import { motion } from "framer-motion";
import { AnimatedNumber } from "@/components/shared/AnimatedNumber";
import { Badge } from "@/components/primitives";
import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  level: string | null | undefined;
  score?: number | null;
  className?: string;
  variant?: "compact" | "detailed";
}

function toneFor(level: string | null | undefined) {
  if (!level) return "neutral" as const;
  const normalised = level.toLowerCase();
  if (normalised === "low") return "low" as const;
  if (normalised === "medium") return "medium" as const;
  if (normalised === "high") return "high" as const;
  return "neutral" as const;
}

export function RiskBadge({ level, score, className, variant = "compact" }: RiskBadgeProps) {
  const tone = toneFor(level);
  return (
    <motion.div
      layout
      className={cn("inline-flex items-center gap-2", className)}
    >
      <Badge tone={tone}>{level ?? "Unknown"}</Badge>
      {score != null && variant === "detailed" && (
        <span className="font-mono text-xs text-[color:var(--color-warm-gray)] flex items-center gap-1">
          <AnimatedNumber value={score * 100} precision={0} suffix="%" />
          <span>match</span>
        </span>
      )}
    </motion.div>
  );
}
