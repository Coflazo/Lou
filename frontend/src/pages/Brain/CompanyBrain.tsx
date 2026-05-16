import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { MagnifyingGlass } from "@phosphor-icons/react";
import { PageHeader } from "@/components/layout";
import { Skeleton, Badge, Input } from "@/components/primitives";
import { BrainGraph, NodePopover } from "@/components/graph";
import { useCompanyBrain } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";
import type { BrainNode } from "@/types";

export function CompanyBrainPage() {
  const brain = useCompanyBrain();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<BrainNode | null>(null);

  const filtered = useMemo(() => {
    if (!brain.data) return { nodes: [], edges: [], metrics: undefined };
    if (!search.trim()) return brain.data;
    const term = search.toLowerCase();
    const nodes = brain.data.nodes.filter((node) => node.label.toLowerCase().includes(term));
    const ids = new Set(nodes.map((node) => node.id));
    const edges = brain.data.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
    return { nodes, edges, metrics: brain.data.metrics };
  }, [brain.data, search]);

  const topByPageRank = useMemo(() => {
    if (!brain.data) return [];
    return [...brain.data.nodes].sort((a, b) => (b.pagerank ?? 0) - (a.pagerank ?? 0)).slice(0, 5);
  }, [brain.data]);

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
              nodes={filtered.nodes}
              edges={filtered.edges}
              width={760}
              height={520}
              onSelect={setSelected}
              className="h-[540px]"
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
              <Metric label="Communities" value={brain.data?.metrics?.communities} />
              <Metric label="Modularity" value={brain.data?.metrics?.modularity?.toFixed(3)} />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="rounded-[18px] bg-surface-raised border border-[color:var(--border-soft)] p-5 flex flex-col gap-3"
          >
            <span className="eyebrow">Top PageRank</span>
            <ul className="flex flex-col divide-y divide-[color:var(--border-soft)]">
              {topByPageRank.map((node) => (
                <li key={node.id} className="py-2 flex items-center justify-between">
                  <span className="text-md text-ink">{node.label}</span>
                  <span className="font-mono text-xs text-[color:var(--color-warm-gray)]">
                    {node.pagerank?.toFixed(3) ?? "—"}
                  </span>
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
              <li>{COPY.BRAIN.LEGEND_PAGERANK}</li>
              <li>{COPY.BRAIN.LEGEND_COMMUNITY}</li>
              <li>{COPY.BRAIN.LEGEND_BETWEENNESS}</li>
            </ul>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string | undefined }) {
  return (
    <div className="flex flex-col">
      <span className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">{label}</span>
      <span className="font-display text-xl text-ink">{value ?? "—"}</span>
    </div>
  );
}
