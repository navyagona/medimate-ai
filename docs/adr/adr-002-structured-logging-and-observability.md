# ADR-002: Standardizing Structured Logging and Zero-Silent-Failure Observability

## Context
In clinical software and medical copilots, unhandled exceptions and silent error swallowing (`try/except pass`) present severe safety and diagnostic risks. Debugging clinical RAG failures, API rate limits, or audio transcription issues without structured context degrades system reliability. MediMate AI requires comprehensive observability across all service boundaries:
- Transparent error propagation and auditability for clinical safety rails.
- Diagnostic tracing for LLM fallbacks, vector database queries, and third-party RxNav API calls.
- Compliance with senior engineering standards ("zero unlogged catches in critical paths").

## Decision
We standardized on Python's standard `logging` module configured at system initialization in `backend/app/config.py`. 

Key architectural requirements implemented:
1. **Module-Scoped Loggers**: Every service module initializes `logger = logging.getLogger(__name__)`.
2. **Explicit Exception Tracing**: Standardized use of `logger.error(..., exc_info=True)` for unhandled service errors, and `logger.warning(...)` for expected operational failovers (e.g. RxNav timeout, Qdrant fallback).
3. **Audit of Silent Catches**: Completely eliminated bare `except Exception: pass` blocks from critical service paths (`routes.py`, `db.py`, `drug_interactions.py`, `llm.py`, `rag.py`).
4. **Structured Format**: Formatted logs include timestamps, log level, module name, and contextual parameters (e.g., patient note IDs, acuity levels, execution modes).

## Consequences
- **Positive**: Full operational transparency during production execution and local testing. Immediate visibility into LLM quota exceedance or network timeouts.
- **Positive**: Easily parseable by cloud log aggregators (Datadog, AWS CloudWatch, Grafana Loki).
- **Negative**: Slightly increased log file volume during high-concurrency evaluation runs.
- **Mitigation**: Log levels are dynamically configurable via the `LOG_LEVEL` environment variable (e.g. `LOG_LEVEL=WARNING` in high-volume production deployments).

## Alternatives Considered
1. **Raw `print()` Statements**: Rejected due to lack of log levels, timestamping, stack trace formatting, and environment-configurable severity filtering.
2. **Third-Party Structural Loggers (e.g., `structlog`, `loguru`)**: Considered, but rejected to maintain zero external C-extension dependencies and keep installation time under 15 minutes.
