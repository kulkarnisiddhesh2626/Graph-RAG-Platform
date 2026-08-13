# Graph-RAG Platform

A lightweight Graph-RAG development platform with document ingestion, knowledge-graph storage, vector retrieval, and a query API.

## Stack

- **FastAPI** — HTTP API
- **ChromaDB** (embedded) — vector store for document chunks
- **NetworkX** — knowledge graph persisted to `data/graph.json`
- **Rule-based extraction** — local development without an LLM API key

## Quick start

```bash
./scripts/cloud-agent-install.sh
./scripts/cloud-agent-start.sh
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Service and index status |
| `/documents` | POST | Ingest text and build graph + vectors |
| `/query` | POST | Graph-augmented retrieval query |
| `/graph` | GET | Knowledge graph snapshot |

### Example

```bash
curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"text":"Alice works at GraphCorp. GraphCorp uses Chroma for vector search."}'

curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Who works at GraphCorp?"}'

curl -s http://localhost:8000/graph
```

## Development

```bash
source .venv/bin/activate
pytest -q
ruff check .
```

## Cloud Agent environment

Repository-managed configuration lives in `.cursor/environment.json`:

- `install` — creates a virtualenv and installs Python dependencies
- `start` — prepares local data directories
- `terminals` — runs the FastAPI dev server on port 8000

Optional secrets:

| Secret | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Future LLM-backed extraction (not required for local demo) |
