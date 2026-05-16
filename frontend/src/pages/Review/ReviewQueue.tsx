import { AnimatePresence, motion } from "framer-motion";
import { Check, X } from "@phosphor-icons/react";
import { useHotkeys } from "react-hotkeys-hook";
import { useState } from "react";
import { PageHeader } from "@/components/layout";
import { Button, Skeleton } from "@/components/primitives";
import { CommitTimeline, ProposalCard } from "@/components/data";
import { EmptyState } from "@/components/shared/EmptyState";
import { useApproveProposal, useCommits, useRejectProposal, useReview } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";

export function ReviewQueuePage() {
  const review = useReview();
  const commits = useCommits();
  const approve = useApproveProposal();
  const reject = useRejectProposal();
  const [activeId, setActiveId] = useState<string | null>(null);

  const items = review.data ?? [];
  const active = items.find((item) => item.id === activeId) ?? items[0] ?? null;

  useHotkeys("a", () => active && approve.mutate({ id: active.id }), [active]);
  useHotkeys("r", () => active && reject.mutate({ id: active.id, reason: "Not aligned" }), [active]);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow="Approval"
        title={COPY.REVIEW.QUEUE_TITLE}
        subtitle={`${COPY.REVIEW.QUEUE_SUBTITLE} ${COPY.REVIEW.SHORTCUTS}`}
      />
      <section className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6">
        <div className="flex flex-col gap-3">
          {review.isLoading ? (
            <Skeleton height="40vh" rounded="18px" />
          ) : items.length === 0 ? (
            <EmptyState title={COPY.REVIEW.EMPTY} icon={<Check size={24} weight="duotone" />} />
          ) : (
            <AnimatePresence mode="popLayout">
              {items.map((proposal) => (
                <motion.div
                  key={proposal.id}
                  onClick={() => setActiveId(proposal.id)}
                  className="cursor-pointer"
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: 60, transition: { duration: 0.2 } }}
                >
                  <ProposalCard
                    proposal={proposal}
                    highlight={active?.id === proposal.id}
                    actions={
                      <>
                        <Button
                          size="sm"
                          variant="primary"
                          loading={approve.isPending && approve.variables?.id === proposal.id}
                          iconLeft={<Check size={14} weight="bold" />}
                          onClick={(event) => {
                            event.stopPropagation();
                            approve.mutate({ id: proposal.id });
                          }}
                        >
                          {COPY.REVIEW.APPROVE}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          loading={reject.isPending && reject.variables?.id === proposal.id}
                          iconLeft={<X size={14} />}
                          onClick={(event) => {
                            event.stopPropagation();
                            reject.mutate({ id: proposal.id, reason: "Not aligned" });
                          }}
                        >
                          {COPY.REVIEW.REJECT}
                        </Button>
                      </>
                    }
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        <aside className="rounded-[18px] bg-surface-raised border border-[color:var(--border-soft)] p-5 flex flex-col gap-4 max-h-[70vh] overflow-y-auto">
          <h3 className="text-xl text-ink">Commits</h3>
          {commits.isLoading ? <Skeleton height="40px" /> : <CommitTimeline commits={commits.data ?? []} />}
        </aside>
      </section>
    </div>
  );
}
