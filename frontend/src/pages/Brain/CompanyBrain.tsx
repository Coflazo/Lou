import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/layout";
import { Skeleton, Badge, Input } from "@/components/primitives";
import { BrainGraph, NodePopover } from "@/components/graph";
import { useCompanyBrain, usePlaybookBrain } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";
import type { BrainNode, MindMapNode } from "@/types";

export function CompanyBrainPage() {
  const brain = useCompanyBrain();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<BrainNode | null>(null);
  const [selectedPlaybookId, setSelectedPlaybookId] = useState<string | undefined>();
  const playbookBrain = usePlaybookBrain(selectedPlaybookId);

  const filtered = useMemo(() => {
    if (!brain.data) return { nodes: [], edges: [], tree: null, metrics: undefined };
    if (!search.trim()) return brain.data;
    const term = search.toLowerCase();
    const nodes = brain.data.nodes.filter((node) => node.label.toLowerCase().includes(term));
    const ids = new Set(nodes.map((node) => node.id));
    const edges = brain.data.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
    return {
      nodes,
      edges,
      tree: brain.data.tree ? filterMindMap(brain.data.tree, term) : null,
      metrics: brain.data.metrics,
    };
  }, [brain.data, search]);

  const branches = useMemo(() => {
    if (!brain.data) return [];
    return brain.data.tree?.children ?? [];
  }, [brain.data]);

  const companyHeight = Math.max(540, branches.length * 126);
  const miniBranches = playbookBrain.data?.tree?.children?.length ?? 0;
  const miniHeight = Math.max(560, miniBranches * 76);
  const miniTitle =
    typeof playbookBrain.data?.tree?.metadata?.full_name === "string"
      ? playbookBrain.data.tree.metadata.full_name
      : playbookBrain.data?.tree?.name ?? "Selected playbook";

  function handleSelect(node: BrainNode | null) {
    setSelected(node);
    const playbookId = playbookIdFromNode(node);
    if (playbookId) {
      setSelectedPlaybookId(playbookId);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Knowledge"
        title={COPY.BRAIN.TITLE}
        subtitle={COPY.BRAIN.SUBTITLE}
        actions={
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={COPY.BRAIN.SEARCH_PLACEHOLDER}
            className="w-72"
          />
        }
      />

      <section className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <div className="relative">
          {brain.isLoading ? (
            <Skeleton height="540px" rounded="20px" />
          ) : (
            <BrainGraph
              tree={filtered.tree}
              width={760}
              height={companyHeight}
              onSelect={handleSelect}
            />
          )}
          <NodePopover node={selected} onClose={() => setSelected(null)} />
        </div>

        <div className="flex flex-col gap-4">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="rounded-[18px] bg-surface-raised border border-[color:var(--border-soft)] p-5 flex flex-col gap-2"
          >
            <span className="eyebrow">Graph metrics</span>
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Nodes" value={brain.data?.metrics?.node_count} />
              <Metric label="Edges" value={brain.data?.metrics?.edge_count} />
              <Metric label="Branches" value={brain.data?.metrics?.branch_count} />
              <Metric label="Relations" value={brain.data?.metrics?.relation_count} />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="rounded-[18px] bg-surface-raised border border-[color:var(--border-soft)] p-5 flex flex-col gap-3"
          >
            <span className="eyebrow">Mind map branches</span>
            <ul className="flex flex-col divide-y divide-[color:var(--border-soft)]">
              {branches.map((node) => (
                <li key={node.id ?? node.name} className="py-2">
                  <button
                    type="button"
                    onClick={() => setSelectedPlaybookId(String(node.metadata?.playbook_id ?? node.id ?? ""))}
                    className="w-full flex items-center justify-between text-left rounded-[8px] px-2 py-1 hover:bg-surface-sunken transition-colors"
                  >
                    <span className="text-md text-ink">{node.name}</span>
                    <span className="font-mono text-xs text-[color:var(--color-warm-gray)]">
                      {node.children?.length ?? 0}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="rounded-[18px] bg-ink text-paper p-5 flex flex-col gap-2"
          >
            <Badge tone="accent">Legend</Badge>
            <ul className="text-base text-[color:oklch(82%_0.008_88)] flex flex-col gap-1">
              <li>{COPY.BRAIN.LEGEND_ROOT}</li>
              <li>{COPY.BRAIN.LEGEND_BRANCH}</li>
              <li>{COPY.BRAIN.LEGEND_LEAF}</li>
            </ul>
          </motion.div>
        </div>
      </section>

      {selectedPlaybookId && (
        <section className="flex flex-col gap-3">
          <div className="flex items-end justify-between gap-4">
            <div>
              <span className="eyebrow">Playbook brain</span>
              <h2 className="text-2xl text-ink font-display">
                {miniTitle}
              </h2>
            </div>
            {playbookBrain.data?.metrics && (
              <span className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">
                {playbookBrain.data.metrics.branch_count} topics
              </span>
            )}
          </div>

          {playbookBrain.isLoading ? (
            <Skeleton height="560px" rounded="20px" />
          ) : (
            <BrainGraph
              tree={playbookBrain.data?.tree}
              width={760}
              height={miniHeight}
              onSelect={setSelected}
            />
          )}
        </section>
      )}
    </div>
  );
}

function playbookIdFromNode(node: BrainNode | null): string | undefined {
  if (!node) return undefined;
  const fromMetadata = node.metadata?.playbook_id;
  if (typeof fromMetadata === "string" && fromMetadata) return fromMetadata;
  if (node.kind === "playbook") return node.id;
  return undefined;
}

function filterMindMap(tree: MindMapNode, term: string): MindMapNode {
  const children = (tree.children ?? [])
    .map((branch) => {
      const leaves = (branch.children ?? []).filter((leaf) => {
        return (
          leaf.name.toLowerCase().includes(term) ||
          leaf.kind?.toLowerCase().includes(term) ||
          leaf.summary?.toLowerCase().includes(term)
        );
      });
      if (branch.name.toLowerCase().includes(term)) return branch;
      if (leaves.length) return { ...branch, children: leaves };
      return null;
    })
    .filter((branch): branch is MindMapNode => Boolean(branch));
  return { ...tree, children };
}

function Metric({ label, value }: { label: string; value: number | string | undefined }) {
  return (
    <div className="flex flex-col">
      <span className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">{label}</span>
      <span className="font-display text-xl text-ink">{value ?? "—"}</span>
    </div>
  );
}
