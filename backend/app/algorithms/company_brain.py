"""Company Brain graph metrics: PageRank, betweenness, and Louvain modularity.

Math
----
PageRank (power iteration):
    PR(v) = (1 - d) / N + d * sum_{u -> v} PR(u) / out_degree(u)
    iterate until ||PR_t - PR_{t-1}||_1 < tol, d = damping factor.

Betweenness centrality (Brandes' algorithm, O(V * E) on unweighted graphs):
    BC(v) = sum_{s != v != t} sigma(s, t | v) / sigma(s, t)

Louvain community detection (greedy modularity maximisation):
    Q = (1 / 2m) * sum_{ij} [A_ij - (k_i * k_j) / 2m] * delta(c_i, c_j)
    Phase 1: greedy node moves to maximise dQ.
    Phase 2: super-node aggregation; repeat until Q stops increasing.

Result is a node-link serialisable JSON payload with metrics attached to every
node so the frontend can size, colour, and weight visual encodings directly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import community as community_louvain
import networkx as nx


@dataclass(frozen=True)
class GraphSnapshot:
    nodes: list[dict]
    edges: list[dict]
    metrics: dict


class CompanyBrainGraph:
    def __init__(
        self,
        pagerank_damping: float = 0.85,
        pagerank_tolerance: float = 1e-6,
        pagerank_max_iterations: int = 200,
    ) -> None:
        self.damping = float(pagerank_damping)
        self.tolerance = float(pagerank_tolerance)
        self.max_iterations = int(pagerank_max_iterations)
        self._cache: tuple[float, GraphSnapshot] | None = None
        self.cache_ttl_seconds: float = 300.0

    def _build_graph(self, entities: Iterable[dict], relations: Iterable[dict]) -> nx.Graph:
        graph = nx.Graph()
        for entity in entities:
            graph.add_node(
                entity["id"],
                label=entity.get("label", entity["id"]),
                kind=entity.get("kind", "entity"),
                metadata=entity.get("metadata", {}),
            )
        for relation in relations:
            source = relation["source"]
            target = relation["target"]
            if source not in graph or target not in graph:
                continue
            graph.add_edge(
                source,
                target,
                label=relation.get("label", "related"),
                weight=float(relation.get("weight", 1.0)),
            )
        return graph

    def _snapshot(self, graph: nx.Graph) -> GraphSnapshot:
        pagerank = nx.pagerank(
            graph,
            alpha=self.damping,
            tol=self.tolerance,
            max_iter=self.max_iterations,
            weight="weight",
        ) if graph.number_of_nodes() else {}

        betweenness = (
            nx.betweenness_centrality(graph, normalized=True, weight="weight")
            if graph.number_of_nodes() > 2
            else {node: 0.0 for node in graph.nodes()}
        )

        communities = community_louvain.best_partition(graph, weight="weight") if graph.number_of_edges() else {
            node: index for index, node in enumerate(graph.nodes())
        }
        modularity = community_louvain.modularity(communities, graph, weight="weight") if graph.number_of_edges() else 0.0

        node_payload: list[dict] = []
        for node_id in graph.nodes():
            data = graph.nodes[node_id]
            node_payload.append(
                {
                    "id": node_id,
                    "label": data.get("label", node_id),
                    "kind": data.get("kind", "entity"),
                    "metadata": data.get("metadata", {}),
                    "pagerank": round(float(pagerank.get(node_id, 0.0)), 6),
                    "betweenness": round(float(betweenness.get(node_id, 0.0)), 6),
                    "community": int(communities.get(node_id, 0)),
                }
            )

        edge_payload: list[dict] = []
        for source, target, data in graph.edges(data=True):
            edge_payload.append(
                {
                    "source": source,
                    "target": target,
                    "label": data.get("label", "related"),
                    "weight": float(data.get("weight", 1.0)),
                }
            )

        return GraphSnapshot(
            nodes=node_payload,
            edges=edge_payload,
            metrics={
                "modularity": round(float(modularity), 6),
                "communities": len(set(communities.values())),
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "density": round(float(nx.density(graph)), 6) if graph.number_of_nodes() else 0.0,
            },
        )

    def compute(
        self,
        entities: Iterable[dict],
        relations: Iterable[dict],
        use_cache: bool = True,
    ) -> GraphSnapshot:
        now = time.time()
        if use_cache and self._cache and now - self._cache[0] < self.cache_ttl_seconds:
            return self._cache[1]
        graph = self._build_graph(entities, relations)
        snapshot = self._snapshot(graph)
        self._cache = (now, snapshot)
        return snapshot

    def invalidate(self) -> None:
        self._cache = None
