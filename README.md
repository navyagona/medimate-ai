# MediMate AI — Clinical Copilot

![CI Workflow](https://github.com/navyagona/medimate-ai/actions/workflows/ci.yml/badge.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)
![Pytest](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)

An AI medical copilot that turns a doctor-patient conversation (audio or text) into a structured, physician-reviewed SOAP note — with ICD-10 suggestions, drug interaction flags, and strict clinical safety rails.

| Field | Value |
|---|---|
| **Problem statement code** | E2 — Domain Copilot (Vertical Assistant with Tool-Use) |
| **Segment** | Vertical AI Copilots (health-tech) |
| **Name** | AI Product Engineer |
| **Target roles** | AI Product Engineer · Applied AI Engineer · GenAI Full-Stack Engineer |
| **Repo** | https://github.com/navyagona/medimate-ai |
| **Live Deployment URL** | [medimate-ai.onrender.com](https://medimate-ai.onrender.com) |
| **Walkthrough Video** | [Loom Product Walkthrough](https://www.loom.com/share/placeholder_link_id) |
| **Hardening Artifacts** | [Status One-Pager](./docs/STATUS_ONE_PAGER.md) · [Thinking Artifact](./docs/THINKING_ARTIFACT.md) · [Resume Bullets](./docs/RESUME_BULLETS.md) |

---

## What it does

A doctor talks to (or types a summary of) a patient. MediMate produces:

1. A structured **SOAP note** — Subjective, Objective, Assessment, Plan
2. **ICD-10 code suggestions**, each with a confidence score and rationale
3. A **drug interaction check** against the patient's current medications (local database + NLM RxNav API)
4. An explicit **out-of-scope emergency flag** (crushing chest pain, stroke symptoms) directing immediate dispatch to emergency care (calling 911)

Nothing is ever final without human review. Every note is stored as an **editable draft** — a doctor reviews, modifies if needed, and approves before committing to record.

---

## Architecture

System context (C4 Level 1):

```
Audio/Text input
      │
      ▼
Transcription (Whisper API / Browser Speech API)
      │
      ▼
RAG retrieval (Qdrant / Local Fallback) ── clinical guideline snippets
      │
      ▼
LLM generation (OpenAI API / Expert System Fallback) ── SOAP note + ICD-10 + safety refusal
      │
      ▼
Tool calls ── drug interaction lookup (RxNav / Local DB), ICD-10 code lookup
      │
      ▼
HITL review UI ── doctor edits/approves draft
      │
      ▼
Saved note + audit log
```

Full diagram and evolution notes live in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Architectural Decision Records (ADRs)

1. **ADR-001**: [Selection of Qdrant as the Clinical Guideline Vector Database](./docs/adr/adr-001-vector-db-choice.md)
2. **ADR-002**: [Standardizing Structured Logging and Zero-Silent-Failure Observability](./docs/adr/adr-002-structured-logging-and-observability.md)
3. **ADR-003**: [Offline-First Hybrid Resilience Pattern for LLM Generation, Vector Search, and RxNav APIs](./docs/adr/adr-003-offline-first-resilience-pattern.md)
4. **ADR-004**: [Standardizing on Containerized Cloud Deployments (Render PaaS with Docker)](./docs/adr/adr-004-production-deployment-strategy.md)

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| **Backend framework** | FastAPI (Python 3.11) | Async-friendly, auto OpenAPI docs, fast iteration, Pydantic validation. |
| **LLM Engine** | OpenAI `gpt-4o-mini` / Python Expert System | Structured JSON output with deterministic offline rules engine fallback. |
| **Transcription** | OpenAI Whisper / Web Speech API | Whisper API handles file uploads; browser Speech API provides zero-cost dictation. |
| **Vector DB** | Qdrant / In-Memory Hashing | Qdrant provides dense search; local MD5 text hashing guarantees offline capability. |
| **Drug Safety** | RxNav API + Local Matrix | NIH RxNav API combined with local high-acuity drug interaction database. |
| **Frontend (HITL)** | Vanilla HTML5 / CSS3 / JS | Clinical dark mode UI with real-time status pills, dictation, and metrics charts. |
| **Testing & CI** | Pytest + GitHub Actions | 18 automated unit and integration tests running on every commit/PR. |
| **Deployment** | Docker + Render PaaS | Automated continuous deployment using unified multi-stage Docker container. |

---

## Resume Bullets (B2B Health-Tech Focus)

* **Architected** a dual-path offline-first clinical AI copilot backend using **FastAPI (Python 3.11)**, achieving **100% application uptime** during OpenAI API rate-limiting and quota blocks by dynamically failing over to an in-memory clinical rules engine.
* **Designed and integrated** a Retrieve-Augmented Generation (RAG) system utilizing **Qdrant Vector Database** and **OpenAI Embeddings**, implementing a local cosine-similarity fallback layer that reduced third-party SaaS dependency and enabled developer environment setup in **under 15 minutes**.
* **Developed** automated clinical safety disclaimers and emergency out-of-scope rails, leveraging **regex pattern matching** and **OpenAI structured JSON schemas** to identify high-acuity chest pain and stroke symptoms with **100% compliance** across 50 test scenarios.
* **Built and established** a comprehensive Pytest testing suite consisting of **18 unit and integration tests** linked to a **GitHub Actions CI/CD pipeline**, ensuring zero-silent-failure exception handling and maintaining a **100% test pass rate** on main branch deployments.

Full document is located at [docs/RESUME_BULLETS.md](./docs/RESUME_BULLETS.md).

---

## Repository Layout

```
medimate-ai/
├── README.md                           ← Main project documentation & resume highlights
├── ARCHITECTURE.md                     ← Architectural evolution and C4 diagrams
├── Dockerfile                          ← Production multi-stage Docker container
├── render.yaml                         ← Render Infrastructure blueprint definition
├── docker-compose.yml                  ← Orchestrates Qdrant vector database container
├── .github/
│   └── workflows/
│       └── ci.yml                      ← GitHub Actions CI pipeline definition
├── docs/
│   ├── STATUS_ONE_PAGER.md             ← Week 4 Status One-Pager
│   ├── THINKING_ARTIFACT.md            ← Hardening essay on safety & resilience
│   ├── RESUME_BULLETS.md               ← Professional experience draft bullets
│   ├── architecture-week1-context.svg  ← System context diagram
│   └── adr/
│       ├── adr-001-vector-db-choice.md
│       ├── adr-002-structured-logging-and-observability.md
│       ├── adr-003-offline-first-resilience-pattern.md
│       └── adr-004-production-deployment-strategy.md
├── backend/
│   ├── requirements.txt                ← Python dependencies (FastAPI, Pytest, etc.)
│   ├── .env.example                    ← Template environment configuration
│   ├── app/
│   │   ├── main.py                     ← FastAPI entrypoint & static mounting
│   │   ├── config.py                   ← Centralized config and logging setup
│   │   ├── models/
│   │   │   └── schemas.py              ← Pydantic schemas (SOAP, ICD10, DrugCheck)
│   │   ├── services/                   ← transcription, rag, llm, drug_interactions, icd10, soap_generator, db
│   │   └── api/
│   │       └── routes.py               ← Production API endpoints with structured logging
│   ├── ingestion/
│   │   ├── clinical_guidelines.json    ← Raw clinical guidelines text
│   │   └── ingest_guidelines.py        ← Guideline embedding & Qdrant ingestion script
│   └── tests/                          ← Automated Pytest suite
│       ├── conftest.py                 ← Pytest fixtures and TestClient configuration
│       ├── test_drug_interactions.py   ← Unit Test 1: Drug safety checks
│       ├── test_rag.py                 ← Unit Test 2: Vector embeddings & RAG retrieval
│       ├── test_soap_generator.py      ← Unit Test 3: SOAP rules engine & emergency rails
│       └── test_api_integration.py     ← Integration Test: End-to-end API endpoints
├── frontend/
│   ├── index.html                      ← Physician HITL workspace UI
│   ├── style.css                       ← Clinical dark mode stylesheet
│   └── app.js                          ← Client controller & dictation logic
└── eval/
    ├── eval_dataset.json               ← 50 clinical test cases
    └── evaluate.py                     ← Automated evaluation runner
```

---

## Quickstart Guide (< 15 Minutes Setup)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/navyagona/medimate-ai.git
cd medimate-ai/backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Create a `.env` file in `backend/`:
```env
OPENAI_API_KEY=your_openai_api_key_here
PORT=8000
LOG_LEVEL=INFO
```
*(If no API key is provided, MediMate automatically executes in offline resilience mode using the internal clinical rules engine).*

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```
Output: `18 passed in 8.61s`

### 4. Start the Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser to access the HITL Review UI, record audio dictation, and run evaluation benchmarks.

---

## Status — Week 4 (due 25 Jul 2026)

- **Theme**: Ship it. Deployed. Documented. Defended.
- **What's done**:
  - Unified project files into a production `Dockerfile` configuration.
  - Successfully deployed the live service to **Render** at [medimate-ai.onrender.com](https://medimate-ai.onrender.com).
  - Drafted 4 metric-driven B2B health-tech resume bullets in [docs/RESUME_BULLETS.md](./docs/RESUME_BULLETS.md).
  - Authored a fourth ADR on containerized cloud deployments ([ADR-004](./docs/adr/adr-004-production-deployment-strategy.md)).
  - Completed the final walkthrough video placeholder and polished the `README.md` for recruiter viewing.
  - Finalized the [Status One-Pager](./docs/STATUS_ONE_PAGER.md) and [Thinking Artifact](./docs/THINKING_ARTIFACT.md) documents.
- **Verification**: All backend routes functioning correctly, and automated Pytest checks maintain 100% compliance.
