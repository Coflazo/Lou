import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import {
  GRAPH_BRANCH_COLORS,
  GRAPH_DEFAULT_HEIGHT_PX,
  GRAPH_DEFAULT_WIDTH_PX,
} from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { BrainNode, MindMapNode } from "@/types";

interface BrainGraphProps {
  tree: MindMapNode | null | undefined;
  width?: number;
  height?: number;
  className?: string;
  onSelect?: (node: BrainNode | null) => void;
}

interface LayoutNode {
  id: string;
  name: string;
  type: "branch" | "leaf";
  kind?: string;
  summary?: string;
  metadata?: Record<string, unknown>;
  x: number;
  y: number;
  depth: number;
  branchIndex: number;
}

interface LayoutEdge {
  source: LayoutNode;
  target: LayoutNode;
}

const BRANCH_COLORS = GRAPH_BRANCH_COLORS;

export function BrainGraph({
  tree,
  width = GRAPH_DEFAULT_WIDTH_PX,
  height = GRAPH_DEFAULT_HEIGHT_PX,
  className,
  onSelect,
}: BrainGraphProps) {
  const [hovered, setHovered] = useState<string | null>(null);
  const layout = useMemo(() => layoutMindMap(tree, width, height), [tree, width, height]);

  return (
    <div
      className={cn("relative w-full overflow-hidden rounded-[20px] bg-surface-raised border border-[color:var(--border-soft)]", className)}
      style={{ height }}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full"
        role="img"
        aria-label="Company brain mind map"
      >
        <g>
          {layout.edges.map((edge, index) => {
            const active = hovered === edge.source.id || hovered === edge.target.id;
            return (
              <motion.path
                key={`${edge.source.id}-${edge.target.id}`}
                d={branchPath(edge.source, edge.target)}
                fill="none"
                stroke={BRANCH_COLORS[edge.target.branchIndex % BRANCH_COLORS.length]}
                strokeOpacity={hovered ? (active ? 0.85 : 0.14) : 0.34}
                strokeWidth={edge.target.depth === 1 ? 2 : 1.4}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ delay: index * 0.02, duration: 0.45 }}
              />
            );
          })}
        </g>

        <g>
          {layout.nodes.map((node) => {
            const isRoot = node.depth === 0;
            const isBranch = node.type === "branch";
            const nodeWidth = isRoot ? 132 : isBranch ? 138 : 166;
            const nodeHeight = isRoot ? 44 : isBranch ? 34 : 30;
            const color = BRANCH_COLORS[node.branchIndex % BRANCH_COLORS.length];
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseEnter={() => setHovered(node.id)}
                onMouseLeave={() => setHovered(null)}
                onClick={() =>
                  onSelect?.({
                    id: node.id,
                    name: node.name,
                    label: node.name,
                    kind: node.kind ?? node.type,
                    type: node.type,
                    summary: node.summary,
                    metadata: node.metadata,
                  })
                }
                className="cursor-pointer"
              >
                <motion.rect
                  x={-nodeWidth / 2}
                  y={-nodeHeight / 2}
                  width={nodeWidth}
                  height={nodeHeight}
                  rx={isRoot ? 18 : 10}
                  fill={isRoot ? "var(--color-ink)" : isBranch ? "var(--surface-sunken)" : "var(--surface-raised)"}
                  stroke={isRoot ? "var(--color-ink)" : color}
                  strokeWidth={isRoot ? 0 : isBranch ? 1.6 : 1}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                />
                {!isRoot && (
                  <circle
                    cx={-nodeWidth / 2 + 12}
                    cy={0}
                    r={3.5}
                    fill={color}
                  />
                )}
                <text
                  x={isRoot ? 0 : -nodeWidth / 2 + 22}
                  y={4}
                  textAnchor={isRoot ? "middle" : "start"}
                  className={isRoot ? "font-display" : "font-mono"}
                  fontSize={isRoot ? 17 : isBranch ? 11 : 10}
                  fill={isRoot ? "var(--color-paper)" : "var(--color-ink)"}
                >
                  {trimLabel(node.name, isRoot ? 16 : isBranch ? 18 : 24)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

function layoutMindMap(tree: MindMapNode | null | undefined, width: number, height: number) {
  if (!tree) return { nodes: [], edges: [] };

  const nodes: LayoutNode[] = [];
  const edges: LayoutEdge[] = [];
  const root = makeNode(tree, width * 0.22, height / 2, 0, 0);
  nodes.push(root);

  const branches = tree.children ?? [];
  const branchGap = height / Math.max(branches.length + 1, 2);

  branches.forEach((branch, branchIndex) => {
    const branchNode = makeNode(branch, width * 0.48, branchGap * (branchIndex + 1), 1, branchIndex);
    nodes.push(branchNode);
    edges.push({ source: root, target: branchNode });

    const leaves = branch.children ?? [];
    const leafGap = Math.min(38, Math.max(14, (branchGap * 0.76) / Math.max(leaves.length - 1, 1)));
    const startY = branchNode.y - (leafGap * (leaves.length - 1)) / 2;

    leaves.forEach((leaf, leafIndex) => {
      const leafNode = makeNode(
        leaf,
        width * 0.78,
        clamp(startY + leafIndex * leafGap, 32, height - 32),
        2,
        branchIndex,
      );
      nodes.push(leafNode);
      edges.push({ source: branchNode, target: leafNode });
    });
  });

  return { nodes, edges };
}

function makeNode(node: MindMapNode, x: number, y: number, depth: number, branchIndex: number): LayoutNode {
  return {
    id: node.id ?? `${depth}-${branchIndex}-${node.name}`,
    name: node.name,
    type: node.type,
    kind: node.kind,
    summary: node.summary,
    metadata: node.metadata,
    x,
    y,
    depth,
    branchIndex,
  };
}

function branchPath(source: LayoutNode, target: LayoutNode): string {
  const mid = source.x + (target.x - source.x) * 0.55;
  return `M ${source.x} ${source.y} C ${mid} ${source.y}, ${mid} ${target.y}, ${target.x} ${target.y}`;
}

function trimLabel(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
