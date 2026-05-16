import { AnimatePresence, motion } from "framer-motion";
import { CaretRight } from "@phosphor-icons/react";
import { useState } from "react";
import { RiskBadge } from "./RiskBadge";
import { truncate, cn } from "@/lib/utils";
import type { ContractFinding } from "@/types";

interface FindingCardProps {
  finding: ContractFinding;
  onSelect?: (finding: ContractFinding) => void;
  active?: boolean;
}

export function FindingCard({ finding, onSelect, active }: FindingCardProps) {
  const [expanded, setExpanded] = useState(false);
  const detailId = `finding-detail-${finding.id}`;
  return (
    <motion.article
      layout
      layoutId={`finding-${finding.id}`}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 320, damping: 26 }}
      role="button"
      tabIndex={0}
      aria-expanded={expanded}
      aria-controls={detailId}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.(finding);
          setExpanded((current) => !current);
        }
      }}
      onClick={() => {
        onSelect?.(finding);
        setExpanded((current) => !current);
      }}
      className={cn(
        "cursor-pointer bg-surface-raised border border-[color:var(--border-soft)] rounded-[14px] px-4 py-3 flex flex-col gap-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-amber)] focus-visible:ring-offset-2",
        active && "border-[color:var(--color-amber)] bg-[color:var(--color-amber-soft)]/35",
        finding.status === "unmapped" && "border-dashed",
      )}
    >
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <motion.span
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.18 }}
            className="text-[color:var(--color-warm-gray)]"
          >
            <CaretRight size={12} />
          </motion.span>
          <h4 className="text-md text-ink truncate">{finding.topic}</h4>
        </div>
        <RiskBadge level={finding.risk} score={finding.match_score} variant="detailed" />
      </header>
      <p className="text-base text-[color:var(--color-ink-soft)]">
        {truncate(finding.excerpt, expanded ? 600 : 140)}
      </p>
      <AnimatePresence>
        {expanded && (
          <motion.div
            id={detailId}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.26, ease: [0.16, 1, 0.3, 1] }}
            className="border-t border-[color:var(--border-soft)] pt-3 mt-2 flex flex-col gap-2"
          >
            <div className="flex justify-between text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
              <span>{finding.location}</span>
              {finding.match_method && <span>method · {finding.match_method}</span>}
            </div>
            <p className="text-base text-ink">{finding.recommendation}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
