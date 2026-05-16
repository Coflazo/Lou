import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import { useEffect, useRef, useState } from "react";
import type { BrainEdge, BrainNode } from "@/types";

interface PositionedNode extends SimulationNodeDatum {
  id: string;
  label: string;
  kind: string;
  pagerank?: number;
  betweenness?: number;
  community?: number;
  metadata?: Record<string, unknown>;
}

interface PositionedLink extends SimulationLinkDatum<PositionedNode> {
  source: string | PositionedNode;
  target: string | PositionedNode;
  weight?: number;
  label?: string;
}

interface GraphState {
  nodes: PositionedNode[];
  links: PositionedLink[];
}

export function useGraphSimulation(
  nodes: BrainNode[],
  edges: BrainEdge[],
  width: number,
  height: number,
): GraphState {
  const [state, setState] = useState<GraphState>({ nodes: [], links: [] });
  const simRef = useRef<Simulation<PositionedNode, PositionedLink> | null>(null);

  useEffect(() => {
    const simNodes: PositionedNode[] = nodes.map((node) => ({
      id: node.id,
      label: node.label,
      kind: node.kind,
      pagerank: node.pagerank,
      betweenness: node.betweenness,
      community: node.community,
      metadata: node.metadata,
      x: node.x ?? width / 2 + (Math.random() - 0.5) * 80,
      y: node.y ?? height / 2 + (Math.random() - 0.5) * 80,
    }));
    const simLinks: PositionedLink[] = edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      weight: edge.weight,
      label: edge.label,
    }));

    const simulation = forceSimulation(simNodes)
      .force("charge", forceManyBody().strength(-260))
      .force(
        "link",
        forceLink<PositionedNode, PositionedLink>(simLinks)
          .id((node) => node.id)
          .distance((link) => 90 + (1 - (link.weight ?? 0.5)) * 80)
          .strength((link) => 0.6 * (link.weight ?? 0.4)),
      )
      .force("center", forceCenter(width / 2, height / 2))
      .force("collide", forceCollide<PositionedNode>().radius((node) => 18 + (node.pagerank ?? 0) * 200))
      .alpha(0.9)
      .alphaDecay(0.06);

    simulation.on("tick", () => {
      setState({ nodes: simNodes.map((node) => ({ ...node })), links: simLinks.map((link) => ({ ...link })) });
    });

    simRef.current = simulation;
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, width, height]);

  return state;
}

export type { PositionedNode, PositionedLink };
