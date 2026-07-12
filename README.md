# MediMate

An AI medical copilot that turns a doctor-patient conversation (audio or text) into a structured, physician-reviewed SOAP note — with ICD-10 suggestions and drug interaction flags.

| Field | Value |
|---|---|
| **Problem statement code** | E2 — Domain Copilot (Vertical Assistant with Tool-Use) |
| **Segment** | Vertical AI Copilots (health-tech) |
| **Name** | AI Product Engineer |
| **Target roles** | AI Product Engineer · Applied AI Engineer · GenAI Full-Stack Engineer |
| **Repo** | https://github.com/navyagona/medimate-ai |

---

## What it does

A doctor talks to (or types a summary of) a patient. MediMate produces:

1. A structured **SOAP note** — Subjective, Objective, Assessment, Plan
2. **ICD-10 code suggestions**, each with a confidence score and rationale
3. A **drug interaction check** against the patient's current medications
4. An explicit **out-of-scope flag** when the case shouldn't be handled by the model at all (pediatric/psychiatric/obstetric emergencies, anything the retrieval layer has no guideline coverage for)

Nothing is ever final. Every note is a **draft** — a doctor reviews, edits if needed, and approves before anything is saved. That approval (and any edits) is logged for audit.

## Why this matters

Vertical copilots — Suki, Abridge, Nabla, DeepScribe, Augmedix in medical; Harvey and Spellbook in legal; Cursor and Devin in code — are where a lot of applied-AI hiring is happening right now. This project is a small, honest version of that pattern: retrieval + structured generation + tool use + human approval + eval, in a domain where a hallucination has to be caught, not hidden.

## Architecture

Full diagram and the Week 1 → Week 2 evolution notes live in [`ARCHITECTURE.md`](./ARCHITECTURE.md). System context (C4 Level 1):

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
LLM generation (OpenAI API) ── SOAP note + ICD-10 + refusal logic, via tool use
      │
      ▼
Tool calls ── drug interaction lookup, ICD-10 code lookup
      │
      ▼
HITL review UI ── doctor edits/approves
      │
      ▼
Saved note + audit log
```

Detailed layout: `![System Context Diagram](./docs/architecture-week1-context.svg)`

## Tech stack

| Component | Choice | Why |
|---|---|---|
| **Backend framework** | FastAPI (Python) | Async-friendly, auto OpenAPI docs, fast to iterate, seamless Pydantic validation. |
| **LLM** | OpenAI API (`gpt-4o-mini`) / Fallback | Strong structured-output + tool-use reliability; follows safety instructions well. Dual-path fallbacks handle quota limitations gracefully. |
| **Transcription** | Whisper / Web Speech API | Whisper API handles file uploads; browser-native Web Speech API allows instant, zero-cost dictation. |
| **Vector DB** | Qdrant / Local Hashing | Qdrant provides dense search for clinical contexts; local in-memory cosine-similarity hashing guarantees offline capability. |
| **Drug interaction** | RxNav API + Fallback | Free, public, no authentication, checks critical drug-drug combinations. |
| **ICD-10 lookup** | Local database + LLM Tool | Free, instant code suggestions mapped directly to medical domains. |
| **Frontend (HITL)** | Plain HTML/CSS/JS | High-fidelity clinical dark mode with responsive workspace editing, status pills, and charts. |
| **Eval** | Custom harness (`/eval`) | Automated script running 50 case summaries, checking SOAP completion, safety disclaimers, and accuracy. |
| **Containerization** | Docker Compose | Spin up Qdrant vector database in a single container. |

Full reasoning for the Qdrant choice: [`docs/adr/adr-001-vector-db-choice.md`](./docs/adr/adr-001-vector-db-choice.md).

## Repo layout

```
mediai/
├── README.md                   ← Week 1 & 2 markdown submissions
├── ARCHITECTURE.md             ← Details architectural decisions and diagrams
├── docker-compose.yml          ← Orchestrates Qdrant container
├── docs/
│   ├── adr/
│   │   └── adr-001-vector-db-choice.md  ← ADR document on vector DB selection
│   └── architecture-week1-context.svg
├── backend/
│   ├── app/
│   │   ├── main.py             ← FastAPI entrypoint
│   │   ├── config.py           ← Config loading and environment parsing
│   │   ├── models/
│   │   │   └── schemas.py      ← Pydantic schemas (SOAP, ICD10, DrugCheck)
│   │   ├── services/           ← transcription, rag, llm, drug_interactions, icd10, soap_generator
│   │   └── api/
│   │       └── routes.py       ← Routes for transcription, soap draft, evals, and logs
│   ├── ingestion/
│   │   ├── clinical_guidelines.json ← Raw guidelines text database
│   │   └── ingest_guidelines.py ← Guideline embedding and ingestion script
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html              ← HITL approval workspace screen
│   ├── style.css               ← Premium clinical style sheet
│   └── app.js                  ← Audio dictation and API client controller
└── eval/
    ├── eval_dataset.json       ← 50 doctor-patient test summaries
    └── evaluate.py             ← CLI pipeline evaluation runner script
```

## Running it locally

### 1. Set up the Environment
Create a `.env` file in `backend/` or set variables directly:
```env
OPENAI_API_KEY=your_key_here
PORT=8000
```
*(If keys are not configured or quota-limited, the system automatically runs in offline/mock mode using clinical heuristics).*

### 2. Stand up Vector DB (Optional)
```bash
docker compose up -d qdrant
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Ingest Guidelines
```bash
python -m ingestion.ingest_guidelines
```

### 5. Start the API
```bash
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) to view the HITL Review UI and run the evaluations.

## Safety

- **No Definitive Diagnoses**: MediMate's Assessment section only reports suspected differentials accompanied by: "Suspected, pending physician verification" disclaimers.
- **Out of Scope Screening**: Detects emergency indicators (e.g. crushing chest pain, slurred speech). If present, sets high acuity, flags the encounter as out of scope, triggers an emergency safety banner in the UI, and directs the doctor to call 911 in the Plan.
- **HITL Review**: Every SOAP note is stored as a draft. Doctors must review and modify fields prior to approving and committing the note to the record.
---

## Status — Week 1 (due 4 Jul 2026)

- **What's done:** Repository structure defined, C4 Level 1 context diagrams created, data layer configured (raw clinical guidelines JSON defined and RAG ingestion scripts written), tech stack finalized, and ADR-001 vector database document completed.
- **What's stuck:** Testing live ingestion against a Qdrant Docker instance (using local in-memory cosine-similarity fallback for text embeddings while Qdrant is initializing).
- **Next week's 3 goals:**
  1. Wire the full end-to-end Python pipeline (audio input → FastAPI → structured SOAP note)
  2. Implement live drug interaction checking via RxNav public API
  3. Stand up the HTML/JS frontend workspace to display drafts and handle physician approvals

## Status — Week 2 (due 11 Jul 2026)

- **What's done:** Complete end-to-end dictation-to-SOAP note flow works with live/fallback API handlers, RAG guidelines integration, ICD-10 suggestions, and drug safety checker. Safety overrides trigger emergency banners for high-acuity cases. HITL approval workflow is fully wired. Automated 50-case evaluation suite created, measuring completeness and safety compliance with metrics visible on the frontend dashboard.
- **What's stuck:** Integrating heavy background noise suppression in Whisper (relying on browser-native Web Speech API for clean dictation capture, which works perfectly for desktop testing).
- **Next week's 3 goals:**
  1. Expand guidelines retrieval databases to include pediatric and psychiatric crisis protocols.
  2. Integrate HL7/FHIR clinical message schema formats in note outputs.
  3. Validate UI workflows with feedback from B2B platform test physicians.
