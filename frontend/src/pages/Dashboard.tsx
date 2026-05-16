import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Files, Headphones, ListChecks } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout";
import { Badge, Button, Skeleton } from "@/components/primitives";
import { CommitTimeline, RiskBadge } from "@/components/data";
import { useCommits, useContracts, usePlaybooks, useReview } from "@/hooks/useApi";
import { useCurrentRole } from "@/hooks/useAuth";
import { AnimatedNumber } from "@/components/shared/AnimatedNumber";
import { formatRelative } from "@/lib/utils";

export function DashboardPage() {
  const role = useCurrentRole();
  const playbooks = usePlaybooks();
  const contracts = useContracts();
  const review = useReview();
  const commits = useCommits();

  const totalPositions = playbooks.data?.reduce((sum, item) => sum + item.position_count, 0) ?? 0;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow={role}
        title="Today in Lou"
        subtitle="Active contracts, pending proposals, and where the playbook stands."
      />

      <section className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Stat label="Playbooks" value={playbooks.data?.length ?? 0} icon={<BookOpen size={16} />} />
          <Stat label="Positions" value={totalPositions} icon={<ListChecks size={16} />} />
          <Stat label="Contracts" value={contracts.data?.length ?? 0} icon={<Files size={16} />} />
        </div>

        <div className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-5 flex flex-col gap-3">
          <span className="eyebrow">Review</span>
          <div className="flex items-baseline gap-3">
            <span className="font-display text-4xl">
              <AnimatedNumber value={review.data?.length ?? 0} />
            </span>
            <span className="text-base text-[color:var(--color-warm-gray)]">proposals pending</span>
          </div>
          <Link to="/review" className="self-start">
            <Button variant="secondary" iconRight={<ArrowRight size={14} />}>
              Open queue
            </Button>
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <div className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-6 flex flex-col gap-4">
          <header className="flex items-center justify-between">
            <h3 className="text-xl text-ink">Recent contracts</h3>
            <Link to="/contracts" className="text-sm font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)] hover:text-ink">
              View all
            </Link>
          </header>
          {contracts.isLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton height="48px" />
              <Skeleton height="48px" />
            </div>
          ) : contracts.data && contracts.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-[color:var(--border-soft)]">
              {contracts.data.slice(0, 5).map((contract, index) => (
                <motion.li
                  key={contract.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="py-3 flex items-center justify-between gap-3"
                >
                  <div className="flex flex-col">
                    <Link to={`/contracts/${contract.id}`} className="text-md text-ink hover:text-[color:var(--color-amber)]">
                      {contract.name}
                    </Link>
                    <span className="text-xs font-mono text-[color:var(--color-warm-gray)]">
                      {contract.finding_count} findings
                    </span>
                  </div>
                  <RiskBadge level={contract.risk_dominant ?? "Medium"} />
                </motion.li>
              ))}
            </ul>
          ) : (
            <p className="text-base text-[color:var(--color-warm-gray)]">Upload a contract to populate this list.</p>
          )}
        </div>

        <div className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-6 flex flex-col gap-4">
          <header className="flex items-center justify-between">
            <h3 className="text-xl text-ink">Voice</h3>
            <Badge tone="accent">Live</Badge>
          </header>
          <p className="text-base text-[color:var(--color-warm-gray)]">
            Capture negotiation calls. Lou turns transcripts into proposals you can approve.
          </p>
          <Link to="/voice" className="self-start">
            <Button iconLeft={<Headphones size={14} weight="fill" />}>Start session</Button>
          </Link>
        </div>
      </section>

      <section className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-6">
        <header className="flex items-center justify-between mb-3">
          <h3 className="text-xl text-ink">Commit history</h3>
          <span className="text-xs font-mono text-[color:var(--color-warm-gray)]">{formatRelative(commits.data?.[0]?.created_at)}</span>
        </header>
        <CommitTimeline commits={commits.data ?? []} />
      </section>
    </div>
  );
}

function Stat({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-5 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <span className="eyebrow">{label}</span>
        <span className="text-[color:var(--color-warm-gray)]">{icon}</span>
      </div>
      <span className="font-display text-4xl">
        <AnimatedNumber value={value} />
      </span>
    </motion.div>
  );
}
