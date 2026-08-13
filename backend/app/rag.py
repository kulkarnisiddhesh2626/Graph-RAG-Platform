from backend.app.extraction import extract_entities_and_relations
from backend.app.graph_store import GraphStore
from backend.app.vector_store import VectorStore


class RagService:
    def __init__(self, graph_store: GraphStore, vector_store: VectorStore) -> None:
        self.graph_store = graph_store
        self.vector_store = vector_store

    def ingest_document(self, document_id: str, text: str) -> dict[str, int | list[str]]:
        entities, relations = extract_entities_and_relations(text)

        for entity in entities:
            self.graph_store.upsert_entity(
                entity.entity_id,
                entity.label,
                entity.entity_type,
                {"source_document": document_id},
            )

        for relation in relations:
            self.graph_store.add_relation(relation.source, relation.target, relation.relation)

        self.graph_store.save()

        from backend.app.extraction import chunk_text

        chunks = chunk_text(text)
        chunk_count = self.vector_store.add_chunks(document_id, chunks)

        return {
            "entities_extracted": len(entities),
            "relations_extracted": len(relations),
            "chunks_indexed": chunk_count,
            "entity_labels": [entity.label for entity in entities],
        }

    def query(self, question: str, limit: int = 5) -> dict[str, object]:
        vector_matches = self.vector_store.query(question, limit=limit)
        graph_matches = self.graph_store.search_entities(question, limit=limit)

        graph_context: list[dict[str, object]] = []
        for match in graph_matches[:3]:
            neighbors = self.graph_store.neighbors(match["id"])
            graph_context.append({"entity": match, "neighbors": neighbors})

        answer_parts = []
        if vector_matches:
            answer_parts.append("Relevant document excerpts:")
            for match in vector_matches[:3]:
                answer_parts.append(f"- {match['text'][:180]}")
        if graph_matches:
            answer_parts.append("Related knowledge graph entities:")
            for match in graph_matches[:3]:
                answer_parts.append(f"- {match['label']} ({match['entity_type']})")

        return {
            "question": question,
            "answer": "\n".join(answer_parts)
            if answer_parts
            else "No indexed knowledge found yet.",
            "vector_matches": vector_matches,
            "graph_matches": graph_matches,
            "graph_context": graph_context,
        }
