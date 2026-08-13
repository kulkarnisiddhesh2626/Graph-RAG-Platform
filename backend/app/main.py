from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.graph_store import GraphStore
from backend.app.rag import RagService
from backend.app.vector_store import VectorStore

graph_store = GraphStore(settings.graph_path)
vector_store = VectorStore(settings.chroma_dir)
rag_service = RagService(graph_store, vector_store)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Graph-RAG Platform", version="0.1.0", lifespan=lifespan)


class DocumentRequest(BaseModel):
    document_id: str | None = None
    text: str = Field(min_length=1)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "graph_nodes": graph_store.graph.number_of_nodes(),
        "graph_edges": graph_store.graph.number_of_edges(),
        "vector_chunks": vector_store.count(),
    }


@app.post("/documents")
def ingest_document(request: DocumentRequest) -> dict[str, Any]:
    document_id = request.document_id or str(uuid4())
    result = rag_service.ingest_document(document_id, request.text)
    return {"document_id": document_id, **result}


@app.post("/query")
def query(request: QueryRequest) -> dict[str, Any]:
    return rag_service.query(request.question, limit=request.limit)


@app.get("/graph")
def graph_snapshot() -> dict[str, Any]:
    return graph_store.snapshot()
