# ADR-004: Standardizing on Containerized Cloud Deployments (Render PaaS with Docker)

## Context
Deploying full-stack B2B domain copilots requires a cloud architecture that handles both dynamic backend logic (FastAPI endpoint calculations, API failover, in-memory evaluations) and static client assets (HTML/CSS/JS HITL workspace). 

We need a deployment model that satisfies the following:
- Extremely fast developer onboarding: "A recruiter should click a link and see it run instantly."
- Standardized packaging: Eliminate environment discrepancies between local environments (Windows, Python 3.11/3.14) and cloud servers (Linux/Ubuntu).
- Zero-cost or low-cost hosting: Fits within a standard free tier.
- Simple environment variable management (safeguarding OpenAI API keys).

## Decision
We standardized on deploying MediMate AI as a **unified Docker container** using **Render's PaaS platform** (Platform-as-a-Service) combined with an Infrastructure-as-Code `render.yaml` blueprint.

Key implementation details:
1. **Unified Docker Context**: The `Dockerfile` copies both `backend` (FastAPI) and `frontend` (static assets) into a single directory structure (`/app`).
2. **FastAPI Static Mount**: FastAPI's `StaticFiles` middleware is used to mount the `/frontend` directory to `/` in the Docker runtime, avoiding the need for a secondary Nginx container or complex CORS routing.
3. **Render Blueprint Configuration**: A root `render.yaml` blueprint defines the service name, build steps (`docker build`), runtime environment (`docker`), exposed ports, and configuration fields.

## Consequences
- **Positive**: Single-command cloud deployments via Render dashboard integration.
- **Positive**: Replicability. Since the deployment is containerized, the running cloud container behaves identically to a local container run, eliminating platform-dependent bugs.
- **Positive**: Free tier friendly. Render allows free hosting of web service containers with auto-scaling to zero when idle.
- **Negative**: Render's free tier has a cold-start delay (web service takes 30-50 seconds to boot from suspension).
- **Mitigation**: Standardized dual-path fallbacks operate immediately upon boot, and a loading notification alerts users to wait for API handshake verification.

## Alternatives Considered
1. **GitHub Pages + Separate Render API**: Rejected because of CORS configuration complexity and the added latency of dual-origin requests for simple prototypes.
2. **Fly.io**: Considered, but rejected due to Render's simpler repository-to-dashboard workflow and more intuitive blueprint YAML definitions for beginner reviewers.
3. **AWS ECS / EKS**: Rejected as over-engineered for recruiter review, introducing slow spin-up times, high maintenance overhead, and non-free cost structures.
