"""Deterministic Company Brain mind-map builder.

The Company Brain used to compute graph-theory metrics and leave layout to a
force simulation. For the demo this is deliberately simpler: one root, grouped
branches, and readable leaves. The payload includes a recursive JSON tree using
the .mm-inspired shape: {"name": "...", "children": [...], "type": "branch"}.
"""

from __future__ import annotations

import time
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MindMapSnapshot:
    nodes: list[dict]
    edges: list[dict]
    tree: dict
    metrics: dict


class CompanyBrainMindMap:
    def __init__(self) -> None:
        self._cache: tuple[float, MindMapSnapshot] | None = None
        self.cache_ttl_seconds: float = 300.0

    def compute(
        self,
        entities: Iterable[dict],
        relations: Iterable[dict],
        use_cache: bool = True,
    ) -> MindMapSnapshot:
        now = time.time()
        if use_cache and self._cache and now - self._cache[0] < self.cache_ttl_seconds:
            return self._cache[1]

        entity_list = list(entities)
        relation_list = list(relations)
        related = _relation_index(relation_list)
        groups: dict[str, list[dict]] = defaultdict(list)
        for entity in entity_list:
            groups[entity.get("kind", "entity")].append(entity)

        nodes: list[dict] = [
            {
                "id": "company-brain",
                "name": "Company Brain",
                "label": "Company Brain",
                "kind": "root",
                "type": "branch",
                "summary": "Legal knowledge map",
                "x": 80.0,
                "y": 260.0,
                "depth": 0,
            }
        ]
        edges: list[dict] = []
        tree_children: list[dict] = []

        group_names = sorted(groups)
        group_gap = 420 / max(len(group_names), 1)
        leaf_x = 520.0

        for group_index, group_name in enumerate(group_names):
            group_id = f"group-{group_name}"
            group_y = 72 + group_index * group_gap
            group_label = _human_group_name(group_name)
            group_entities = sorted(groups[group_name], key=lambda item: item.get("label", item["id"]))
            branch_children: list[dict] = []

            nodes.append(
                {
                    "id": group_id,
                    "name": group_label,
                    "label": group_label,
                    "kind": "group",
                    "type": "branch",
                    "summary": f"{len(group_entities)} item{'s' if len(group_entities) != 1 else ''}",
                    "x": 285.0,
                    "y": round(group_y, 2),
                    "depth": 1,
                    "metadata": {"kind": group_name, "count": len(group_entities)},
                }
            )
            edges.append({"source": "company-brain", "target": group_id, "label": group_label, "kind": "branch"})

            leaf_gap = min(58.0, 250.0 / max(len(group_entities), 1))
            start_y = group_y - leaf_gap * (len(group_entities) - 1) / 2
            for entity_index, entity in enumerate(group_entities):
                entity_id = entity["id"]
                relation_notes = related.get(entity_id, [])
                summary = _summary_for(entity, relation_notes)
                nodes.append(
                    {
                        "id": entity_id,
                        "name": entity.get("label", entity_id),
                        "label": entity.get("label", entity_id),
                        "kind": entity.get("kind", "entity"),
                        "type": "leaf",
                        "summary": summary,
                        "metadata": {
                            **entity.get("metadata", {}),
                            "relations": len(relation_notes),
                        },
                        "x": leaf_x,
                        "y": round(start_y + entity_index * leaf_gap, 2),
                        "depth": 2,
                        "group": group_id,
                    }
                )
                edges.append({"source": group_id, "target": entity_id, "label": "contains", "kind": "branch"})
                branch_children.append(
                    {
                        "id": entity_id,
                        "name": entity.get("label", entity_id),
                        "type": "leaf",
                        "kind": entity.get("kind", "entity"),
                        "summary": summary,
                        "metadata": {**entity.get("metadata", {}), "relations": len(relation_notes)},
                    }
                )

            tree_children.append(
                {
                    "id": group_id,
                    "name": group_label,
                    "type": "branch",
                    "kind": "group",
                    "summary": f"{len(group_entities)} item{'s' if len(group_entities) != 1 else ''}",
                    "children": branch_children,
                }
            )

        snapshot = MindMapSnapshot(
            nodes=nodes,
            edges=edges,
            tree={
                "id": "company-brain",
                "name": "Company Brain",
                "type": "branch",
                "kind": "root",
                "summary": "Legal knowledge map",
                "children": tree_children,
            },
            metrics={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "branch_count": len(group_names),
                "relation_count": len(relation_list),
            },
        )
        self._cache = (now, snapshot)
        return snapshot

    def from_playbooks(self, playbooks: Iterable[object], use_cache: bool = True) -> MindMapSnapshot:
        now = time.time()
        if use_cache and self._cache and now - self._cache[0] < self.cache_ttl_seconds:
            return self._cache[1]

        playbook_list = list(playbooks)
        branch_children: list[dict] = []
        relation_count = 0
        for playbook in sorted(playbook_list, key=lambda item: getattr(item, "name", "")):
            related = _related_playbooks(playbook, playbook_list)
            relation_count += len(related)
            branch_children.append(
                {
                    "id": getattr(playbook, "id"),
                    "name": _short_playbook_name(getattr(playbook, "name")),
                    "type": "branch",
                    "kind": "playbook",
                    "summary": getattr(playbook, "description", ""),
                    "metadata": {
                        "playbook_id": getattr(playbook, "id"),
                        "category": getattr(playbook, "category", ""),
                        "full_name": getattr(playbook, "name", ""),
                        "topic_count": len(getattr(playbook, "positions", [])),
                        "related_playbooks": related,
                    },
                    "children": [
                        {
                            "id": f"topic-{position.id}",
                            "name": _short_topic_name(position.topic),
                            "type": "leaf",
                            "kind": "topic",
                            "summary": position.preferred_position,
                            "metadata": {
                                "playbook_id": getattr(playbook, "id"),
                                "position_id": position.id,
                                "risk": position.risk,
                            },
                        }
                        for position in getattr(playbook, "positions", [])
                    ],
                }
            )

        snapshot = _snapshot_from_tree(
            {
                "id": "company-brain",
                "name": "Company Brain",
                "type": "branch",
                "kind": "root",
                "summary": "Playbook-level legal memory",
                "children": branch_children,
            }
        )
        relation_edges = _playbook_relation_edges(branch_children)
        snapshot.edges.extend(relation_edges)
        snapshot.metrics["edge_count"] = len(snapshot.edges)
        snapshot.metrics["relation_count"] = len(relation_edges) or relation_count
        self._cache = (now, snapshot)
        return snapshot

    def from_playbook(self, playbook: object) -> MindMapSnapshot:
        children: list[dict] = []
        for position in getattr(playbook, "positions", []):
            leaf_children = [
                {
                    "id": f"{position.id}-preferred",
                    "name": "Preferred",
                    "type": "leaf",
                    "kind": "preferred",
                    "summary": position.preferred_position,
                    "metadata": {"position_id": position.id, "playbook_id": getattr(playbook, "id")},
                },
                {
                    "id": f"{position.id}-fallback",
                    "name": "Fallback",
                    "type": "leaf",
                    "kind": "fallback",
                    "summary": position.fallback_position,
                    "metadata": {"position_id": position.id, "playbook_id": getattr(playbook, "id")},
                },
            ]
            red_line = _column_value(position.columns, "Red Line")
            deal_breaker = _column_value(position.columns, "Deal Breaker")
            if red_line:
                leaf_children.append(
                    {
                        "id": f"{position.id}-red-line",
                        "name": "Red Line",
                        "type": "leaf",
                        "kind": "red-line",
                        "summary": red_line,
                        "metadata": {"position_id": position.id, "playbook_id": getattr(playbook, "id")},
                    }
                )
            if deal_breaker:
                leaf_children.append(
                    {
                        "id": f"{position.id}-deal-breaker",
                        "name": "Deal Breaker",
                        "type": "leaf",
                        "kind": "deal-breaker",
                        "summary": deal_breaker,
                        "metadata": {"position_id": position.id, "playbook_id": getattr(playbook, "id")},
                    }
                )
            if position.keywords:
                leaf_children.append(
                    {
                        "id": f"{position.id}-keywords",
                        "name": "Keywords",
                        "type": "leaf",
                        "kind": "keywords",
                        "summary": ", ".join(position.keywords[:6]),
                        "metadata": {"position_id": position.id, "playbook_id": getattr(playbook, "id")},
                    }
                )

            children.append(
                {
                    "id": f"topic-{position.id}",
                    "name": _short_topic_name(position.topic),
                    "type": "branch",
                    "kind": "topic",
                    "summary": position.topic,
                    "metadata": {
                        "playbook_id": getattr(playbook, "id"),
                        "position_id": position.id,
                        "risk": position.risk,
                    },
                    "children": leaf_children,
                }
            )

        return _snapshot_from_tree(
            {
                "id": getattr(playbook, "id"),
                "name": _playbook_root_name(playbook),
                "type": "branch",
                "kind": "playbook",
                "summary": getattr(playbook, "description", ""),
                "metadata": {
                    "playbook_id": getattr(playbook, "id"),
                    "category": getattr(playbook, "category", ""),
                    "full_name": getattr(playbook, "name", ""),
                },
                "children": children,
            }
        )

    def invalidate(self) -> None:
        self._cache = None


def _relation_index(relations: list[dict]) -> dict[str, list[str]]:
    related: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        source = relation.get("source")
        target = relation.get("target")
        label = relation.get("label", "related")
        if source and target:
            related[source].append(f"{label}: {target}")
            related[target].append(f"{label}: {source}")
    return related


def _human_group_name(kind: str) -> str:
    words = kind.replace("_", " ").replace("-", " ").split()
    if not words:
        return "Entities"
    label = " ".join(word.capitalize() for word in words)
    if label.endswith("y"):
        return f"{label[:-1]}ies"
    if label.endswith("s"):
        return label
    return f"{label}s"


def _summary_for(entity: dict, relations: list[str]) -> str:
    metadata = entity.get("metadata", {})
    if metadata:
        first_key = next(iter(metadata))
        return f"{first_key}: {metadata[first_key]}"
    if relations:
        return relations[0]
    return entity.get("kind", "entity")


def _snapshot_from_tree(tree: dict) -> MindMapSnapshot:
    nodes: list[dict] = []
    edges: list[dict] = []

    def walk(node: dict, depth: int, parent_id: str | None = None) -> None:
        node_id = node.get("id") or f"{parent_id or 'root'}-{len(nodes)}"
        payload = {
            "id": node_id,
            "name": node.get("name", node_id),
            "label": node.get("name", node_id),
            "kind": node.get("kind", node.get("type", "leaf")),
            "type": node.get("type", "leaf"),
            "summary": node.get("summary", ""),
            "metadata": node.get("metadata", {}),
            "depth": depth,
        }
        nodes.append(payload)
        if parent_id:
            edges.append({"source": parent_id, "target": node_id, "label": "contains", "kind": "branch"})
        for child in node.get("children", []) or []:
            walk(child, depth + 1, node_id)

    walk(tree, 0)
    branch_count = sum(1 for node in nodes if node.get("type") == "branch") - 1
    return MindMapSnapshot(
        nodes=nodes,
        edges=edges,
        tree=tree,
        metrics={
            "node_count": len(nodes),
            "edge_count": len(edges),
            "branch_count": max(branch_count, 0),
            "relation_count": 0,
        },
    )


def _short_playbook_name(name: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", name)
    words = [
        word
        for word in re.findall(r"[A-Za-z0-9]+", cleaned)
        if word.lower() not in {"siemens", "standard", "sample", "demo", "playbook"}
    ]
    if not words:
        return name[:28]
    if "NDA" in {word.upper() for word in words}:
        selected = [word for word in words if word.upper() in {"NDA"} or word.lower() in {"mutual", "vendor"}]
        return " ".join(selected[:3]) or "NDA"
    return " ".join(words[:3])


def _playbook_root_name(playbook: object) -> str:
    category = getattr(playbook, "category", "")
    if category:
        return _short_playbook_name(category)
    return _short_playbook_name(getattr(playbook, "name", "Playbook"))


def _short_topic_name(topic: str) -> str:
    words = re.findall(r"[A-Za-z0-9-]+", topic)
    return " ".join(words[:3]) if words else topic[:28]


def _column_value(columns: dict[str, str], name: str) -> str:
    normalised = re.sub(r"[^a-z0-9]", "", name.lower())
    for key, value in columns.items():
        if re.sub(r"[^a-z0-9]", "", key.lower()) == normalised:
            return value
    return ""


def _related_playbooks(playbook: object, playbooks: list[object]) -> list[dict]:
    source_terms = _playbook_terms(playbook)
    related: list[dict] = []
    for candidate in playbooks:
        if getattr(candidate, "id") == getattr(playbook, "id"):
            continue
        overlap = sorted(source_terms & _playbook_terms(candidate))
        if overlap or getattr(candidate, "category", "") == getattr(playbook, "category", ""):
            related.append(
                {
                    "playbook_id": getattr(candidate, "id"),
                    "name": _short_playbook_name(getattr(candidate, "name")),
                    "reason": ", ".join(overlap[:4]) or "same category",
                }
            )
    return related[:4]


def _playbook_relation_edges(playbook_nodes: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    edges: list[dict] = []
    for node in playbook_nodes:
        source = node.get("id")
        if not source:
            continue
        for related in node.get("metadata", {}).get("related_playbooks", []):
            target = related.get("playbook_id")
            if not target:
                continue
            pair = tuple(sorted([source, target]))
            if pair in seen:
                continue
            seen.add(pair)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "label": related.get("reason", "related"),
                    "kind": "bond",
                    "strength": 0.5,
                }
            )
    return edges


def _playbook_terms(playbook: object) -> set[str]:
    terms = {getattr(playbook, "category", "").lower()}
    for position in getattr(playbook, "positions", []):
        terms.update(keyword.lower() for keyword in position.keywords)
        terms.update(word.lower() for word in re.findall(r"[A-Za-z][A-Za-z-]{4,}", position.topic))
    return {term for term in terms if term}
