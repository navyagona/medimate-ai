# ADR-001: Selection of Qdrant as the Clinical Guideline Vector Database

## Context
Our medical copilot **MediMate** requires a vector database to perform Retrieval-Augmented Generation (RAG) over clinical guidelines (e.g. NICE, GINA, ICD-10 chapters). The search must be highly relevant, latency must remain low, and the system must be easily testable by B2B development teams in local, containerized, and staging environments. We need a vector DB that supports:
- Fast hybrid keyword/vector search.
- Lightweight memory footprint.
- Simple Docker container orchestration.
- Offline developer capability without external SaaS dependencies.

## Decision
We chose **Qdrant** as our primary vector database, accompanied by a **local JSON in-memory vector fallback** implemented directly in Python. 

### Why Qdrant:
- **Rust-powered Performance**: Outstanding speed, memory efficiency, and search precision.
- **Easy Self-Hosting**: Standard Docker image is setup in one step.
- **Rich Filtering & Hybrid Search**: Supports combined payload filters and vector metrics.
- **Robust Client SDKs**: Official, well-maintained `qdrant-client` package for Python.

### Why the Local Fallback:
- Direct support for offline-first testing environments where Docker may not be installed.
- Zero installation overhead for instant startup within 15 seconds.

## Consequences
- **Positive**: Single command database deployments (`docker compose up -d qdrant`). Offline fallback ensures tests and frontends execute seamlessly under all environments.
- **Negative**: Adds minor code complexity to maintain the dual-path RAG service in `backend/app/services/rag.py`.
- **Mitigation**: Fallback calculations are encapsulated inside the RAG service, presenting an identical interface to the rest of the application.

## Alternatives considered
1. **Pinecone (SaaS)**: Rejected because it requires active internet connections, accounts, API keys, and has high network roundtrip latencies for local demos.
2. **FAISS (Facebook AI Similarity Search)**: Rejected due to heavy C++ binary dependencies which frequently fail to compile/install on standard Windows environments.
3. **ChromaDB**: Considered, but rejected due to occasional SQLite file locking issues on Windows and larger storage footprint compared to Qdrant's lightweight container.
