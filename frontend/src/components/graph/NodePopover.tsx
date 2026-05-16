import { motion, AnimatePresence } from "framer-motion";
import { X } from "@phosphor-icons/react";
import { Badge } from "@/components/primitives";
import type { BrainNode } from "@/types";

interface NodePopoverProps {
  node: BrainNode | null;
  onClose: () => void;
}

export function NodePopover({ node, onClose }: NodePopoverProps) {
  return (
    <AnimatePresence>
      {node && (
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 6 }}
          transition={{ type: "spring", stiffness: 280, damping: 22 }}
          className="absolute right-6 top-6 w-72 bg-surface-raised border border-[color:var(--border-soft)] rounded-[14px] shadow-[var(--shadow-3)] p-4 flex flex-col gap-3"
        >
          <header className="flex items-start justify-between gap-2">
            <div className="flex flex-col gap-1">
              <span className="eyebrow">{node.kind}</span>
              <h3 className="text-xl text-ink">{node.label}</h3>
            </div>
            <button onClick={onClose} className="p-1 rounded-[6px] hover:bg-surface-sunken">
              <X size={14} />
            </button>
          </header>
          <div className="grid grid-cols-3 gap-2">
            <Metric label="PageRank" value={node.pagerank} />
            <Metric label="Between" value={node.betweenness} />
            <Metric label="Comm" value={node.community} integer />
          </div>
          {node.metadata && Object.keys(node.metadata).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(node.metadata).map(([key, value]) => (
                <Badge key={key} tone="neutral">
                  {key} · {String(value)}
                </Badge>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Metric({ label, value, integer }: { label: string; value: number | undefined; integer?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="eyebrow">{label}</span>
      <span className="font-mono text-md text-ink">
        {value == null ? "—" : integer ? value.toString() : value.toFixed(3)}
      </span>
    </div>
  );
}
