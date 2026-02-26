# GRC-AI-Automation

AI-augmented vendor onboarding pipeline for Security Governance, Risk, and Compliance (GRC).

Automates the four-stage vendor due diligence workflow — Use Case Evaluation, Legal/Regulatory Review, Security Risk Evaluation, and Financial Risk Review — using RAG-powered LLM analysis, a human-in-the-loop approval workflow, and a full audit trail.

---

## Architecture

```
INTAKE
  → USE_CASE_REVIEW        (Stage 1 — human form)
  → USE_CASE_APPROVED
  → LEGAL_REVIEW           (Stage 2 — AI + RAG)
  → LEGAL_APPROVED
  → NDA_PENDING
  → SECURITY_REVIEW        (Stage 3 — AI + RAG)
  → SECURITY_APPROVED
  → FINANCIAL_REVIEW       (Stage 4 — human form)
  → FINANCIAL_APPROVED
  → ONBOARDED
  / REJECTED               (exit from any stage)
```

**Stack:** FastAPI · Gunicorn (UvicornWorker) · SQLAlchemy / SQLite · ChromaDB · sentence-transformers · litellm · React + TypeScript

---

## Quickstart

### Option A — Docker Compose

```bash
git clone <repo-url>
cd vendor-onboarding
cp .env.example .env        # add your ANTHROPIC_API_KEY
docker compose up
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### Option B — Local (backend only)

```bash
cd vendor-onboarding/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example ../.env  # add your ANTHROPIC_API_KEY

# Run with Gunicorn (production-style)
gunicorn -c gunicorn.conf.py main:app

# Or single-process for development
uvicorn main:app --reload
```

### Frontend (Day 6)

```bash
cd vendor-onboarding/frontend
npm install
npm run dev
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | LLM provider (`anthropic` or `openai`) |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model ID passed to litellm |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic provider |
| `OPENAI_API_KEY` | — | Required for OpenAI provider or `text-embedding-3-small` |
| `DATABASE_URL` | `sqlite:///./vendor_onboarding.db` | SQLAlchemy database URL |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | ChromaDB persistence directory |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model (local) or `text-embedding-3-small` (OpenAI) |

---

## API Overview

Full interactive documentation is available at `/docs` (Swagger UI) or `/redoc`.

### Vendors

| Method | Path | Description |
|---|---|---|
| `POST` | `/vendors/` | Create a vendor (enters INTAKE state) |
| `GET` | `/vendors/` | List all vendors |
| `GET` | `/vendors/{id}` | Get vendor by ID |
| `POST` | `/vendors/{id}/confirm-nda` | Confirm NDA — advances LEGAL_APPROVED → SECURITY_REVIEW |
| `POST` | `/vendors/{id}/complete-onboarding` | Finalise onboarding (FINANCIAL_APPROVED → ONBOARDED) |
| `POST` | `/vendors/{id}/reject` | Reject vendor from any stage |

### Documents

| Method | Path | Description |
|---|---|---|
| `POST` | `/vendors/{id}/documents` | Upload a document for a workflow stage |
| `GET` | `/vendors/{id}/documents` | List documents for a vendor |
| `GET` | `/documents/{id}` | Get document by ID |

### Reviews

| Method | Path | Description |
|---|---|---|
| `GET` | `/vendors/{id}/reviews` | List all reviews for a vendor |
| `GET` | `/reviews/{id}` | Get review by ID |
| `POST` | `/reviews/{id}/trigger` | Trigger AI analysis (Stages 2 and 3) |
| `POST` | `/reviews/{id}/submit-form` | Submit human form (Stage 1 / Stage 4) |

### Decisions

| Method | Path | Description |
|---|---|---|
| `POST` | `/reviews/{id}/decisions` | Record APPROVE / REJECT / APPROVE_WITH_CONDITIONS |
| `GET` | `/reviews/{id}/decisions` | List decisions for a review |

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## Project Structure

```
vendor-onboarding/
├── backend/
│   ├── main.py                          # FastAPI app + lifespan handler
│   ├── gunicorn.conf.py                 # Gunicorn configuration
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/routes/
│   │   ├── vendors.py
│   │   ├── documents.py
│   │   ├── reviews.py
│   │   └── decisions.py
│   ├── core/
│   │   ├── config.py                    # Pydantic settings
│   │   ├── database.py                  # SQLAlchemy engine + session
│   │   └── models.py                    # ORM models + enums
│   ├── schemas/
│   │   ├── vendor.py
│   │   ├── document.py
│   │   ├── review.py
│   │   ├── decision.py
│   │   └── forms.py                     # UseCaseFormInput, FinancialRiskFormInput
│   └── services/
│       ├── workflow.py                  # WorkflowService (orchestration)
│       ├── llm/client.py                # litellm wrapper
│       ├── document/
│       │   ├── extractor.py             # PDF/DOCX/text → raw text
│       │   └── chunker.py               # raw text → chunks
│       ├── rag/
│       │   ├── embedder.py              # text → vectors
│       │   ├── store.py                 # ChromaDB wrapper
│       │   └── retriever.py             # query → context string
│       ├── knowledge_base/
│       │   ├── legal_kb.py              # regulatory requirement entries
│       │   ├── security_kb.py           # security control entries
│       │   └── loader.py                # seeds KB into ChromaDB on startup
│       ├── legal/analyzer.py            # Stage 2 AI module
│       └── security/analyzer.py         # Stage 3 AI module
├── frontend/                            # Vite + React + TypeScript (Day 6)
├── .env.example
└── docker-compose.yml
```

---

## Development Roadmap

| Day | Focus | Status |
|---|---|---|
| 1 | Architecture, scaffolding, data models | ✅ Complete |
| 2 | Document ingestion, LLM abstraction, RAG layer | Pending |
| 3 | Stage 2: Legal / Regulatory AI module | Pending |
| 4 | Stage 3: Security Risk AI module + NDA gate | Pending |
| 5 | Workflow orchestration, human-form stages, audit log | Pending |
| 6 | React frontend | Pending |
| 7 | Mock data, testing, demo polish | Pending |

---

## Demo Data (Day 7)

```bash
# Seed three pre-built vendor scenarios
curl -X POST http://localhost:8000/dev/seed
```

- **Acme Analytics** — clean pass across all four stages
- **DataFlow Inc.** — fails Stage 2 on GDPR Article 28 gap
- **SecureVault Ltd.** — conditional pass (security + financial flags)
