import { motion } from "framer-motion";
import { scaleLinear, scaleOrdinal, scaleSqrt } from "d3-scale";
import { useMemo, useState } from "react";
import { useGraphSimulation } from "@/hooks/useGraph";
import { cn } from "@/lib/utils";
import type { BrainEdge, BrainNode } from "@/types";

interface BrainGraphProps {
  nodes: BrainNode[];
  edges: BrainEdge[];
  width?: number;
  height?: number;
  className?: string;
  onSelect?: (node: BrainNode | null) => void;
}

const COMMUNITY_COLORS = [
  "var(--color-amber)",
  "var(--color-green)",
  "var(--color-red)",
  "var(--color-ink)",
  "var(--color-warm-gray)",
];

export function BrainGraph({ nodes, edges, width = 720, height = 480, className, onSelect }: BrainGraphProps) {
  const [hovered, setHovered] = useState<string | null>(null);
  const sim = useGraphSimulation(nodes, edges, width, height);

  const radius = useMemo(() => {
    const values = nodes.map((node) => node.pagerank ?? 0);
    return scaleSqrt<number>().domain([Math.min(...values, 0), Math.max(...values, 0.01)]).range([8, 26]);
  }, [nodes]);

  const stroke = useMemo(() => {
    const values = nodes.map((node) => node.betweenness ?? 0);
    return scaleLinear<number>().domain([Math.min(...values, 0), Math.max(...values, 0.01)]).range([0.5, 3.5]);
  }, [nodes]);

  const color = useMemo(() => {
    return scaleOrdinal<number, string>()
      .domain(Array.from(new Set(nodes.map((node) => node.community ?? 0))))
      .range(COMMUNITY_COLORS);
  }, [nodes]);

  return (
    <div className={cn("relative w-full overflow-hidden rounded-[20px] bg-surface-raised border border-[color:var(--border-soft)]", className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        role="img"
        aria-label="Company brain knowledge graph"
      >
        <g>
          {sim.links.map((link, index) => {
            const source = link.source as { id?: string; x?: number; y?: number };
            const target = link.target as { id?: string; x?: number; y?: number };
            if (!source.x || !target.x) return null;
            return (
              <motion.line
                key={`${source.id}-${target.id}-${index}`}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="var(--border-soft)"
                strokeOpacity={hovered ? (hovered === source.id || hovered === target.id ? 0.9 : 0.18) : 0.5}
                strokeWidth={1}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: Math.min(index, 80) * 0.005, duration: 0.6 }}
              />
            );
          })}
        </g>
        <g>
          {sim.nodes.map((node, index) => {
            const r = Math.max(10, radius(node.pagerank ?? 0));
            const isHovered = hovered === node.id;
            return (
              <motion.g
                key={node.id}
                transform={`translate(${node.x ?? 0}, ${node.y ?? 0})`}
                onMouseEnter={() => setHovered(node.id)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => onSelect?.(nodes.find((item) => item.id === node.id) ?? null)}
                initial={{ scale: 0.4, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: Math.min(index, 60) * 0.015, type: "spring", stiffness: 220, damping: 18 }}
                className="cursor-pointer"
              >
                <motion.circle
                  r={r}
                  fill={color(node.community ?? 0)}
                  stroke="var(--color-ink)"
                  strokeWidth={stroke(node.betweenness ?? 0)}
                  animate={{ r: isHovered ? r * 1.18 : r }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                />
                <text
                  y={r + 12}
                  textAnchor="middle"
                  className="font-mono"
                  fontSize="10"
                  fill="var(--color-ink-soft)"
                >
                  {node.label}
                </text>
              </motion.g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
