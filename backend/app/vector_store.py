from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings


class VectorStore:
    """Embedded ChromaDB collection for document chunks."""

    def __init__(self, persist_dir: Path) -> None:
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, document_id: str, chunks: list[str]) -> int:
        if not chunks:
            return 0

        ids = [f"{document_id}:{index}" for index in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "chunk_index": index} for index in range(len(chunks))
        ]
        self.collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        return len(chunks)

    def query(self, query_text: str, limit: int = 5) -> list[dict[str, str | float]]:
        if self.collection.count() == 0:
            return []

        result = self.collection.query(
            query_texts=[query_text], n_results=min(limit, self.collection.count())
        )
        documents = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]

        matches: list[dict[str, str | float]] = []
        for document, distance, metadata in zip(documents, distances, metadatas, strict=True):
            matches.append(
                {
                    "text": document,
                    "document_id": str(metadata.get("document_id", "")),
                    "score": round(1 - float(distance), 4),
                }
            )
        return matches

    def count(self) -> int:
        return self.collection.count()
