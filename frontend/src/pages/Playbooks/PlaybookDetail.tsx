import { useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { PencilSimple, FloppyDisk, X } from "@phosphor-icons/react";
import { PageHeader, SplitPane } from "@/components/layout";
import { Button, Skeleton, Textarea, Badge } from "@/components/primitives";
import { ClauseRow, RiskBadge } from "@/components/data";
import { usePlaybook, useUpdatePosition } from "@/hooks/useApi";
import { useRoleGate } from "@/hooks/useAuth";
import { COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { PlaybookPosition } from "@/types";

export function PlaybookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: playbook, isLoading } = usePlaybook(id);
  const update = useUpdatePosition();
  const canEdit = useRoleGate("SENIOR");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [editing, setEditing] = useState<PlaybookPosition | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});

  if (isLoading || !playbook) return <Skeleton height="60vh" rounded="18px" />;

  const active = playbook.positions.find((position) => position.id === activeId) ?? playbook.positions[0];

  function startEdit(position: PlaybookPosition) {
    setEditing(position);
    setDraft({ ...position.columns });
  }

  async function save() {
    if (!editing || !playbook) return;
    await update.mutateAsync({ playbookId: playbook.id, positionId: editing.id, columns: draft });
    setEditing(null);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow={playbook.category}
        title={playbook.name}
        subtitle={COPY.PLAYBOOKS.DETAIL_SUBTITLE}
        actions={
          <div className="flex items-center gap-2">
            <Badge tone="accent">{playbook.positions.length} positions</Badge>
          </div>
        }
      />

      <SplitPane
        leftWidth="minmax(280px, 360px)"
        rightWidth="minmax(0, 1fr)"
        collapseAt="md"
        left={
          <div className="flex flex-col gap-1 max-h-[70vh] overflow-y-auto pr-1">
            {playbook.positions.map((position) => (
              <ClauseRow
                key={position.id}
                position={position}
                active={active?.id === position.id}
                onClick={() => setActiveId(position.id)}
              />
            ))}
          </div>
        }
        right={
          <AnimatePresence mode="wait">
            {active && (
              <motion.section
                key={active.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ type: "spring", stiffness: 220, damping: 24 }}
                className="rounded-[20px] bg-surface-raised border border-[color:var(--border-soft)] p-6 flex flex-col gap-5"
              >
                <header className="flex items-start justify-between gap-4">
                  <div className="flex flex-col gap-2">
                    <span className="eyebrow">Topic</span>
                    <h2 className="text-2xl text-ink font-display">{active.topic}</h2>
                  </div>
                  <RiskBadge level={active.risk} />
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <PositionBlock title="Preferred position" body={active.preferred_position} tone="success" />
                  <PositionBlock title="Fallback ladder" body={active.fallback_position} tone="medium" />
                </div>

                <div className="flex flex-col gap-2">
                  <span className="eyebrow">Columns</span>
                  <table className="w-full text-base">
                    <tbody>
                      {playbook.columns.map((column) => (
                        <tr key={column} className="border-b border-[color:var(--border-soft)] last:border-b-0">
                          <td className="py-2 pr-4 font-mono uppercase text-xs tracking-wider text-[color:var(--color-warm-gray)] w-44">
                            {column}
                          </td>
                          <td className="py-2 text-ink">{active.columns[column] || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {active.keywords?.map((keyword) => (
                    <Badge key={keyword} tone="neutral">{keyword}</Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between border-t border-[color:var(--border-soft)] pt-4">
                  <span className="text-xs font-mono uppercase tracking-wider text-[color:var(--color-warm-gray)]">
                    {canEdit ? COPY.PLAYBOOKS.EDIT_HINT : COPY.PLAYBOOKS.EDIT_GATE}
                  </span>
                  {canEdit && (
                    <Button
                      variant="secondary"
                      iconLeft={<PencilSimple size={14} />}
                      onClick={() => startEdit(active)}
                    >
                      Edit position
                    </Button>
                  )}
                </div>
              </motion.section>
            )}
          </AnimatePresence>
        }
      />

      <AnimatePresence>
        {editing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-[color:var(--surface-overlay)]"
            onClick={() => setEditing(null)}
          >
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 220, damping: 26 }}
              onClick={(event) => event.stopPropagation()}
              className="absolute right-0 top-0 bottom-0 w-full max-w-xl bg-surface-base p-8 overflow-y-auto"
            >
              <header className="flex items-start justify-between mb-6">
                <div>
                  <span className="eyebrow">Edit position</span>
                  <h2 className="text-2xl font-display">{editing.topic}</h2>
                </div>
                <button onClick={() => setEditing(null)} className="p-2 rounded-[8px] hover:bg-surface-sunken">
                  <X size={14} />
                </button>
              </header>
              <div className="flex flex-col gap-4">
                {playbook.columns.map((column) => (
                  <Textarea
                    key={column}
                    label={column}
                    value={draft[column] ?? ""}
                    onChange={(event) => setDraft({ ...draft, [column]: event.target.value })}
                  />
                ))}
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <Button variant="ghost" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
                <Button onClick={save} loading={update.isPending} iconLeft={<FloppyDisk size={14} />}>
                  Save
                </Button>
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function PositionBlock({ title, body, tone }: { title: string; body: string; tone: "success" | "medium" }) {
  return (
    <div
      className={cn(
        "rounded-[14px] p-4 flex flex-col gap-2",
        tone === "success" ? "bg-[color:var(--color-green-soft)]/40" : "bg-[color:var(--color-amber-soft)]/40",
      )}
    >
      <span className="eyebrow">{title}</span>
      <p className="text-base text-ink">{body}</p>
    </div>
  );
}
