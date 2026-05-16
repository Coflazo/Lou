import { motion } from "framer-motion";
import { Badge } from "@/components/primitives";
import { cn, formatRelative } from "@/lib/utils";
import type { Proposal } from "@/types";

interface ProposalCardProps {
  proposal: Proposal;
  actions?: React.ReactNode;
  highlight?: boolean;
  className?: string;
}

export function ProposalCard({ proposal, actions, highlight, className }: ProposalCardProps) {
  const sourceBadge = proposal.source === "voice" ? "accent" : proposal.source === "contract" ? "medium" : "neutral";
  const matchSummary = proposal.voice_match_scores?.matches?.[0];

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 80, transition: { duration: 0.24 } }}
      transition={{ type: "spring", stiffness: 220, damping: 24 }}
      className={cn(
        "bg-surface-raised rounded-[16px] border border-[color:var(--border-soft)] p-4 flex flex-col gap-3 transition-colors",
        highlight && "border-[color:var(--color-amber)]",
        className,
      )}
    >
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge tone={sourceBadge}>{proposal.source}</Badge>
          <Badge tone={proposal.status === "approved" ? "success" : proposal.status === "rejected" ? "high" : "neutral"}>
            {proposal.status}
          </Badge>
        </div>
        <span className="font-mono text-xs uppercase text-[color:var(--color-warm-gray)]">
          {formatRelative(proposal.created_at)}
        </span>
      </header>
      <h3 className="text-xl text-ink">{proposal.topic}</h3>
      <p className="text-base text-[color:var(--color-ink-soft)]">{proposal.proposed_text}</p>
      <p className="text-sm text-[color:var(--color-warm-gray)] italic">{proposal.rationale}</p>
      {matchSummary && (
        <div className="font-mono text-xs text-[color:var(--color-warm-gray)] flex items-center gap-3 flex-wrap">
          <span>match {Math.round(matchSummary.score * 100)}%</span>
          <span>jw {matchSummary.jaro.toFixed(2)}</span>
          <span>tfidf {matchSummary.tfidf.toFixed(2)}</span>
          <span>edit {matchSummary.edit.toFixed(2)}</span>
        </div>
      )}
      {actions && <footer className="flex items-center gap-2 pt-1">{actions}</footer>}
    </motion.article>
  );
}
