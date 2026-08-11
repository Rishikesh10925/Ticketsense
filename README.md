# TicketSense

TicketSense is an enterprise-grade, multi-tenant, multi-agent AI support intelligence platform that turns support tickets into explainable, evidence-grounded, confidence-aware resolutions while converting successful support interactions into organizational knowledge.

## Run locally

Requirements: Docker Desktop with Compose v2.

```bash
copy .env.example .env
docker compose up --build
```

- Web application: http://localhost:3000
- FastAPI/OpenAPI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

Compose starts pgvector/PostgreSQL, applies all Alembic migrations, creates development accounts, loads the curated knowledge base, starts FastAPI, and serves the production React build.

## Demo accounts

All development accounts use `Demo@123`.

| Portal | Account |
|---|---|
| Customer | `customer@demo.com` |
| Support agent | `agent@demo.com` |
| Manager | `manager@demo.com` |
| Enterprise admin | `admin@demo.com` |
| AI administrator | `aiadmin@demo.com` |
| Knowledge manager | `knowledge@demo.com` |
| Security administrator | `security@demo.com` |

Never use these credentials outside local development.

## End-to-end resolution flow

1. JWT-authenticated customer submits a ticket.
2. Preprocessing detects and redacts PII from the AI-safe representation.
3. Specialized stages understand, classify, score priority/SLA, detect duplicates, retrieve evidence, propose root causes, validate policy and safety, calculate confidence, and select routing.
4. Retrieval is restricted by organization and department.
5. The decision gate selects auto-resolution eligibility, human review, or expert escalation. High-risk work is never automatically resolved.
6. Every agent decision, evidence item, action and safe explanation is persisted for resolution replay and observability.
7. Agent actions, customer feedback, incidents, knowledge gaps and generated articles feed the learning workflow.

The default deterministic provider keeps the complete workflow runnable without a paid API. `ai/agents/llm_interface.py` provides the configurable provider boundary for OpenAI-compatible, local, Gemini-compatible or Anthropic-compatible implementations.

## Main APIs

- `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`
- `POST /api/tickets`, `GET /api/tickets`, `GET /api/tickets/{id}`
- `POST /api/tickets/{id}/action`, `POST /api/tickets/{id}/feedback`
- `GET /api/tickets/{id}/ai-analysis`, `/evidence`, `/similar`, `/trace`
- `GET /api/knowledge`, article generation and approval endpoints
- `GET /api/analytics`, `/api/ai/metrics`, `/api/incidents`
- `GET /api/audit-logs`, `/api/notifications`, `/api/integrations`

All protected resources are scoped by the authenticated user's `tenant_id`. Role guards protect elevated operations.

## Project layout

```text
backend/       FastAPI, SQLAlchemy models, schemas, services, routers, tests
ai/            provider abstraction, LangGraph pipeline, embeddings and ML training
frontend/      React + TypeScript enterprise role-aware workspace
db/            Alembic migrations, organization/demo seed, curated knowledge
data/          privacy-safe synthetic ticket generation and import tools
docs/          architecture and research evaluation protocol
docker-compose.yml
```

## Development checks

```bash
cd frontend
npm install
npm run build

cd ../backend
uv sync --extra dev
uv run pytest
```

For optional training and pgvector embedding tools, use `uv sync --extra ai`.

## Research positioning

Individual techniques such as classification, RAG and routing are established. TicketSense's contribution is their integrated, measurable decision workflow: cross-source evidence, multi-agent validation, risk-aware autonomy, contradiction handling, incident and knowledge-gap detection, resolution replay, and feedback-to-knowledge learning. See [research-evaluation.md](docs/research-evaluation.md) for the experiment matrix and leakage-safe evaluation protocol.

## Security notes

JWTs, bcrypt, tenant checks, RBAC, input validation, PII redaction, rate limiting, CORS, security headers and audit records are included. Change `JWT_SECRET_KEY`, database credentials, allowed origins and provider secrets before any non-local deployment. Secrets must remain server-side.
