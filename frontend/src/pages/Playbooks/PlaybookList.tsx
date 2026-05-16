import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight, BookOpen } from "@phosphor-icons/react";
import { PageHeader } from "@/components/layout";
import { Skeleton } from "@/components/primitives";
import { EmptyState } from "@/components/shared/EmptyState";
import { usePlaybooks } from "@/hooks/useApi";
import { COPY } from "@/lib/constants";
import { useMemo, useState } from "react";

export function PlaybookListPage() {
  const playbooks = usePlaybooks();
  const [filter, setFilter] = useState<string>("all");

  const categories = useMemo(() => {
    const set = new Set<string>();
    playbooks.data?.forEach((item) => set.add(item.category));
    return ["all", ...Array.from(set).sort()];
  }, [playbooks.data]);

  const visible = useMemo(() => {
    if (!playbooks.data) return [];
    return filter === "all" ? playbooks.data : playbooks.data.filter((item) => item.category === filter);
  }, [playbooks.data, filter]);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader eyebrow="Library" title={COPY.PLAYBOOKS.LIST_TITLE} subtitle={COPY.PLAYBOOKS.LIST_SUBTITLE} />

      <div className="flex items-center gap-2 flex-wrap">
        {categories.map((category) => (
          <motion.button
            key={category}
            onClick={() => setFilter(category)}
            whileTap={{ scale: 0.96 }}
            className={`px-3 py-1.5 rounded-[8px] font-mono text-xs uppercase tracking-wider transition-colors ${
              filter === category ? "bg-ink text-paper" : "bg-surface-sunken text-[color:var(--color-warm-gray)] hover:text-ink"
            }`}
          >
            {category}
          </motion.button>
        ))}
      </div>

      {playbooks.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} height="220px" rounded="18px" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <EmptyState icon={<BookOpen size={28} />} title={COPY.PLAYBOOKS.EMPTY} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {visible.map((playbook, index) => (
            <motion.div
              key={playbook.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, type: "spring", stiffness: 220, damping: 22 }}
              whileHover={{ y: -4 }}
            >
              <Link
                to={`/playbooks/${playbook.id}`}
                className="block rounded-[18px] border border-[color:var(--border-soft)] bg-surface-raised p-6 transition-shadow hover:shadow-[var(--shadow-3)]"
              >
                <span className="eyebrow">{playbook.category}</span>
                <h3 className="text-2xl text-ink font-display mt-2">{playbook.name}</h3>
                <p className="text-base text-[color:var(--color-ink-soft)] mt-2 mb-6 line-clamp-3">
                  {playbook.description}
                </p>
                <div className="flex items-end justify-between">
                  <div className="flex flex-col">
                    <span className="font-mono text-xs uppercase tracking-wider text-[color:var(--color-warm-gray)]">positions</span>
                    <span className="font-display text-3xl">{playbook.position_count}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <ArrowUpRight size={18} className="text-[color:var(--color-amber)]" weight="bold" />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
