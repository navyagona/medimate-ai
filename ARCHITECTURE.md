# MediMate Architecture Specification

This document details the software architecture, data pipelines, and security mechanisms of the **MediMate** clinical assistant.

---

## 🏗️ System Architecture (C4 Level 2 - Container Diagram)

```mermaid
graph TB
    subgraph Client [Client Browser Tier]
        UI[HITL Web UI - HTML/CSS/JS]
        Speech[Web Speech API - Native Dictation]
    end

    subgraph Server [FastAPI Application Tier]
        App[FastAPI Server - app/main.py]
        Routes[API Routes - app/api/routes.py]
        SoapOrch[SOAP Note Generator Service]
        RAGService[RAG Guidelines Client]
        LLMAgent[OpenAI Agent / Offline Expert System]
        DrugCheck[RxNav Drug Interaction Checker]
    end

    subgraph Data [Storage & External APIs]
        QdrantDB[(Qdrant Vector DB - Guidelines)]
        LocalDB[(Local DB - JSON - Saved Notes)]
        OpenAIAPI[OpenAI API - gpt-4o-mini]
        RxNavAPI[RxNav REST API]
    end

    %% Client and Server Connections
    UI -->|1. Transmit Audio/Text| Routes
    Speech -->|Native Speech-to-Text| UI
    Routes --> SoapOrch

    %% Server Internal Orchestration
    SoapOrch -->|2. Get Guidelines| RAGService
    RAGService -->|Query Vectors| QdrantDB
    SoapOrch -->|3. Suggest Codes & Draft| LLMAgent
    LLMAgent -->|Tool Use: Check Drugs| DrugCheck
    DrugCheck -->|Query API| RxNavAPI
    LLMAgent -->|LLM Prompt| OpenAIAPI
    
    %% Save Flow
    UI -->|4. Approve SOAP Note| Routes
    Routes --> LocalDB
```

---

## 🔄 Core Data Pipeline Flow

```
   ┌────────────────────────────────────────────────────────┐
   │ 1. User Encounters Patient (Speak Audio / Type Summary)│
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │ 2. Transcription Stage: Whisper API or Local Mock      │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │ 3. RAG Retrieval Stage: Embed text and query guidelines│
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │ 4. Tool Execution: Check drug safety & ICD-10 suggestions│
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │ 5. LLM Synthesis Stage: Draft structured SOAP note     │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │ 6. HITL Screen: Physician reviews, edits, and saves    │
   └───────────────────────────┬────────────────────────────┘
```

### 1. Ingestion Pipeline
Before the copilot is active, clinical guidelines from sources like NICE are converted to chunks, embedded using OpenAI's embedding API (`text-embedding-3-small` or hashed offline), and loaded into a Qdrant collection named `guidelines` (or cache file).

### 2. Retrieval Pipeline (RAG)
During an active session:
- The input transcript is embedded using the same vector representation.
- Qdrant (or local fallback) retrieves the top 3 most relevant clinical guideline passages.
- The retrieved guidelines are formatted as context and injected into the LLM system prompt.

### 3. Agentic Decisions & Tool Use
The agent leverages tool-use schemas:
- **`get_drug_interactions`**: Calls RxNav API to check safety profiles.
- **`get_icd10_codes`**: Formulates recommendations for ICD-10 coding.
- **`get_guideline_rag`**: Obtains context about medical rules.
- **`get_diagnostic_tests`**: Suggests standard tests.

### 4. Safety Guardrails
- **Refusal System**: If the clinical case is evaluated as an active high-acuity crisis (e.g. myocardial infarction or acute stroke), the generator triggers an out-of-scope flag. The FastAPI backend returns a safety warning payload, prompting the UI to render a warning banner directing the clinician to activate emergency transport.
- **Audit-ready Storage**: Finalized notes, including full edit diffs and doctor identifiers, are logged for compliance.
