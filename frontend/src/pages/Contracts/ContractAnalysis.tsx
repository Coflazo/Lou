import { useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { PageHeader, SplitPane } from "@/components/layout";
import { Skeleton } from "@/components/primitives";
import { FindingCard, RiskPosteriorBar } from "@/components/data";
import { useContract } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";
import { cn, riskToColor, riskToSoftColor } from "@/lib/utils";
import type { ContractFinding } from "@/types";

export function ContractAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const { data: contract, isLoading } = useContract(id);
  const [activeFinding, setActiveFinding] = useState<string | null>(null);
  const documentRef = useRef<HTMLDivElement>(null);

  const sortedFindings = useMemo(() => {
    if (!contract) return [];
    const order: Record<string, number> = { High: 0, Medium: 1, Low: 2 };
    return [...contract.findings].sort((a, b) => {
      const r = (order[a.risk] ?? 9) - (order[b.risk] ?? 9);
      if (r !== 0) return r;
      return (b.match_score ?? 0) - (a.match_score ?? 0);
    });
  }, [contract]);

  function focusFinding(finding: ContractFinding) {
    setActiveFinding(finding.id);
    const target = documentRef.current?.querySelector(`[data-finding="${finding.id}"]`) as HTMLElement | null;
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  if (isLoading || !contract) return <Skeleton height="70vh" rounded="20px" />;

  const renderedDocument = renderHighlighted(contract.text, contract.highlights, activeFinding);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Contract"
        title={contract.name}
        subtitle={`${contract.findings.length} findings · ${contract.sections.length} sections`}
      />

      {contract.risk_posterior && (
        <div className="rounded-[16px] bg-surface-raised border border-[color:var(--border-soft)] px-5 py-4">
          <RiskPosteriorBar posterior={contract.risk_posterior} />
        </div>
      )}

      <SplitPane
        leftWidth="minmax(0, 1.4fr)"
        rightWidth="minmax(0, 1fr)"
        gap="32px"
        left={
          <article
            ref={documentRef}
            className="rounded-[20px] bg-surface-raised border border-[color:var(--border-soft)] p-6 max-h-[70vh] overflow-y-auto text-base text-ink leading-relaxed whitespace-pre-wrap"
          >
            {renderedDocument}
          </article>
        }
        right={
          <div className="flex flex-col gap-3">
            <header className="flex items-center justify-between">
              <h3 className="text-xl text-ink">{COPY.ANALYSIS.FINDINGS_LABEL}</h3>
              <span className="text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
                {contract.findings.length}
              </span>
            </header>
            <AnimatePresence mode="popLayout">
              {sortedFindings.map((finding) => (
                <FindingCard
                  key={finding.id}
                  finding={finding}
                  onSelect={focusFinding}
                  active={activeFinding === finding.id}
                />
              ))}
            </AnimatePresence>
            {sortedFindings.length === 0 && (
              <p className="text-base text-[color:var(--color-warm-gray)]">{COPY.ANALYSIS.NO_FINDINGS}</p>
            )}
          </div>
        }
      />
    </div>
  );
}

function renderHighlighted(text: string, highlights: { id: string; finding_id: string; start: number; end: number; risk?: string }[], active: string | null) {
  if (!highlights.length) return text;
  const sorted = [...highlights].sort((a, b) => a.start - b.start);
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  sorted.forEach((highlight) => {
    if (highlight.start > cursor) {
      parts.push(<span key={`text-${cursor}`}>{text.slice(cursor, highlight.start)}</span>);
    }
    const isActive = active === highlight.finding_id;
    parts.push(
      <motion.mark
        key={highlight.id}
        layout
        data-finding={highlight.finding_id}
        style={{
          background: isActive ? riskToSoftColor(highlight.risk) : "transparent",
          borderBottom: `2px solid ${riskToColor(highlight.risk)}`,
        }}
        className={cn(
          "px-0.5 transition-colors cursor-pointer",
          isActive && "rounded-[3px]",
        )}
      >
        {text.slice(highlight.start, highlight.end)}
      </motion.mark>,
    );
    cursor = highlight.end;
  });
  if (cursor < text.length) parts.push(<span key={`text-${cursor}`}>{text.slice(cursor)}</span>);
  return parts;
}
