import { motion } from "framer-motion";
import { riskToColor } from "@/lib/utils";
import type { RiskPosterior } from "@/types";

interface RiskPosteriorBarProps {
  posterior: RiskPosterior;
}

export function RiskPosteriorBar({ posterior }: RiskPosteriorBarProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">
        <span>Risk posture</span>
        <span>{posterior.dominant} dominant</span>
      </div>
      <div className="flex h-3 w-full rounded-full overflow-hidden bg-surface-sunken">
        {posterior.levels.map((label, index) => {
          const value = posterior.mean[index] ?? 0;
          return (
            <motion.div
              key={label}
              initial={{ width: 0 }}
              animate={{ width: `${value * 100}%` }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: index * 0.08 }}
              style={{ background: riskToColor(label) }}
              className="h-full"
            />
          );
        })}
      </div>
      <div className="grid grid-cols-3 gap-2 mt-1">
        {posterior.levels.map((label) => {
          const ci = posterior.credible_intervals[label] ?? [0, 0];
          return (
            <div key={label} className="text-xs font-mono text-[color:var(--color-warm-gray)] flex flex-col gap-0.5">
              <span className="text-[color:var(--color-ink-soft)] tracking-wider uppercase">{label}</span>
              <span>{(ci[0] * 100).toFixed(0)}–{(ci[1] * 100).toFixed(0)}% CI</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
