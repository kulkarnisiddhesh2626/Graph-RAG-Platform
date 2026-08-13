import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    graph_path = tmp_path / "graph.json"
    chroma_dir = tmp_path / "chroma"
    monkeypatch.setenv("GRAPH_PATH", str(graph_path))
    monkeypatch.setenv("CHROMA_DIR", str(chroma_dir))

    from backend.app import config

    config.settings = config.Settings(
        data_dir=tmp_path,
        graph_path=graph_path,
        chroma_dir=chroma_dir,
    )

    from backend.app.graph_store import GraphStore
    from backend.app.main import graph_store, rag_service, vector_store
    from backend.app.vector_store import VectorStore

    new_graph = GraphStore(graph_path)
    new_vector = VectorStore(chroma_dir)
    graph_store.graph = new_graph.graph
    graph_store.path = graph_path
    vector_store.collection = new_vector.collection
    vector_store.client = new_vector.client
    rag_service.graph_store = graph_store
    rag_service.vector_store = vector_store

    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_ingest_and_query(client):
    ingest = client.post(
        "/documents",
        json={
            "text": (
                "Alice works at GraphCorp. GraphCorp uses Neo4j and Chroma for Graph RAG pipelines."
            ),
        },
    )
    assert ingest.status_code == 200
    ingest_payload = ingest.json()
    assert ingest_payload["entities_extracted"] >= 2
    assert ingest_payload["chunks_indexed"] >= 1

    query = client.post("/query", json={"question": "Alice GraphCorp"})
    assert query.status_code == 200
    payload = query.json()
    assert "Alice" in payload["answer"] or payload["graph_matches"]

    graph = client.get("/graph")
    assert graph.status_code == 200
    graph_payload = graph.json()
    assert graph_payload["node_count"] >= 2
