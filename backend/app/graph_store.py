import json
from pathlib import Path
from typing import Any

import networkx as nx


class GraphStore:
    """Persistent knowledge graph backed by NetworkX and JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.graph = nx.MultiDiGraph()
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.graph = nx.node_link_graph(payload, directed=True, multigraph=True)

    def save(self) -> None:
        payload = nx.node_link_data(self.graph)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert_entity(
        self, entity_id: str, label: str, entity_type: str, metadata: dict[str, Any]
    ) -> None:
        self.graph.add_node(
            entity_id,
            label=label,
            entity_type=entity_type,
            **metadata,
        )

    def add_relation(self, source: str, target: str, relation: str) -> None:
        self.graph.add_edge(source, target, relation=relation)

    def neighbors(self, entity_id: str) -> list[dict[str, Any]]:
        if entity_id not in self.graph:
            return []

        results: list[dict[str, Any]] = []
        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor)
            relation = "related_to"
            if edge_data:
                first_edge = next(iter(edge_data.values()))
                relation = first_edge.get("relation", relation)
            node = self.graph.nodes[neighbor]
            results.append(
                {
                    "id": neighbor,
                    "label": node.get("label", neighbor),
                    "entity_type": node.get("entity_type", "unknown"),
                    "relation": relation,
                }
            )
        return results

    def search_entities(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_lower = query.lower()
        matches: list[dict[str, Any]] = []
        for node_id, data in self.graph.nodes(data=True):
            label = str(data.get("label", node_id))
            if query_lower in label.lower() or query_lower in node_id.lower():
                matches.append(
                    {
                        "id": node_id,
                        "label": label,
                        "entity_type": data.get("entity_type", "unknown"),
                    }
                )
            if len(matches) >= limit:
                break
        return matches

    def snapshot(self) -> dict[str, Any]:
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "nodes": [
                {
                    "id": node_id,
                    "label": data.get("label", node_id),
                    "entity_type": data.get("entity_type", "unknown"),
                }
                for node_id, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "relation": data.get("relation", "related_to"),
                }
                for source, target, data in self.graph.edges(data=True)
            ],
        }
