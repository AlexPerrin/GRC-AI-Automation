# GRC-AI-Automation

AI-augmented vendor onboarding pipeline for Security Governance, Risk, and Compliance (GRC). Automates a four-stage due diligence workflow — Use Case, Legal/Regulatory, Security Risk, and Financial Risk — using RAG-powered LLM analysis with a human-in-the-loop approval flow and full audit trail.

**Backend:** FastAPI · Gunicorn (UvicornWorker) · SQLAlchemy / SQLite · ChromaDB · LangChain · LiteLLM

**Frontend:** React 18 · TypeScript · Vite · Tailwind CSS · TanStack Query · React Router

## Quickstart

```bash
git clone git@github.com:AlexPerrin/GRC-AI-Automation.git
cd GRC-AI-Automation
cp .env.example .env        # fill in LLM_PROVIDER_API_KEY
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ChromaDB | `http://localhost:8001` |

### Frontend dev server (without Docker)

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 — proxies /api to localhost:8000
```

---

## Testing

Tests use an isolated in-memory SQLite database and mocked service boundaries — no external services (ChromaDB, LLM API) required.

```bash
cd backend

# Run the full suite
.venv/bin/python -m pytest tests/ -v

# Single module
.venv/bin/python -m pytest tests/test_api_documents.py -v
```

| Module | Tests | Covers |
|---|---|---|
| `test_config.py` | 6 | `llm_model_string` for all providers, `chroma_use_server` toggle |
| `test_models.py` | 11 | ORM creation, FK relationships, cascade deletes, enum completeness |
| `test_schemas.py` | 17 | Pydantic validation — valid payloads, rejected values, required fields |
| `test_api_vendors.py` | 17 | Vendor CRUD, pagination, 404s, stub endpoints, health check |
| `test_api_documents.py` | 10 | Upload 201, raw_text persistence, chroma_collection_id, 404s, list, get |
| `test_api_reviews.py` | 10 | List/get reviews, trigger AI analysis, 404s |
| `test_api_workflow.py` | 21 | Intake, form submission, decisions, financial review, onboarding, reject |
| `test_llm_client.py` | 7 | JSON parsing, markdown fence stripping, invalid JSON error |
| `test_extractor.py` | 6 | PDF/DOCX/TXT extraction, None page text, non-UTF-8 bytes |
| `test_chunker.py` | 7 | Long text splitting, metadata preservation, chunk_index, empty input |
| `test_embedder.py` | 6 | Shape, lazy loading, model reuse, normalize flag |
| `test_vector_store.py` | 7 | Upsert IDs/docs, query returns docs, collection_exists true/false |
| `test_retriever.py` | 5 | Separator joining, n forwarding, single/empty chunk edge cases |
| `test_kb_loader.py` | 5 | Skip when exists, seed when absent, partial seed, entry_id in metadata |
| `test_legal_analyzer.py` | 9 | Return type, findings structure, edge cases, call counts |
| `test_security_analyzer.py` | 10 | Return type, domain/gap structure, edge cases, call counts |
| `test_workflow_intake.py` | 17 | create_vendor_and_intake, submit use case form, start financial review |
| `test_workflow_legal.py` | 7 | Trigger legal review success/error, audit log events |
| `test_workflow_security.py` | 11 | Confirm NDA, NDA gate, trigger security review success/error |
| `test_workflow_decisions.py` | 26 | Legal/security/financial decisions, onboarding, reject, state transitions |
| **Total** | **215** | |

---

## Environment Variables

Copy `.env.example` to `.env` and set `LLM_PROVIDER_API_KEY`. All other values have working defaults.

### LLM

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | Provider: `anthropic`, `openai`, or `openrouter` |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model ID passed to litellm |
| `LLM_PROVIDER_API_KEY` | — | API key for the selected provider |

| `LLM_PROVIDER` | `LLM_MODEL` | Notes |
|---|---|---|
| `anthropic` | `claude-sonnet-4-6` | Direct Anthropic API |
| `openai` | `gpt-4o` | Direct OpenAI API |
| `openrouter` | `anthropic/claude-sonnet-4-6` | Via OpenRouter |
| `openrouter` | `meta-llama/llama-3.1-70b-instruct` | Via OpenRouter |

### Database & Storage

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./vendor_onboarding.db` | Overridden to a named volume path in Docker |
| `CHROMA_HOST` | _(empty)_ | Leave blank for local embedded mode; set to `chromadb` in Docker |
| `CHROMA_PORT` | `8000` | ChromaDB server port (Docker only) |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | Local persistence path (embedded mode only) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model |

### Docker — Frontend

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_PORT` | `5173` | Host port mapped to the frontend container |
| `BACKEND_HOST` | `api` | Hostname the nginx proxy forwards `/api` requests to |
| `BACKEND_PORT` | `8000` | Backend port used by the nginx proxy |

---

## API Overview

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

### Vendors

| Method | Path | Description |
|---|---|---|
| `POST` | `/vendors/` | Create a vendor (enters INTAKE state) |
| `GET` | `/vendors/` | List all vendors (paginated) |
| `GET` | `/vendors/{id}` | Get vendor by ID |
| `POST` | `/vendors/{id}/start-intake` | Open Stage 1 Use Case review |
| `POST` | `/vendors/{id}/confirm-nda` | Confirm NDA — advances LEGAL_APPROVED → SECURITY_REVIEW |
| `POST` | `/vendors/{id}/start-financial-review` | Open Stage 4 Financial review |
| `POST` | `/vendors/{id}/complete-onboarding` | Finalise onboarding |
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

### Audit

| Method | Path | Description |
|---|---|---|
| `GET` | `/vendors/{id}/audit-logs` | List all audit events for a vendor (newest first) |

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## Project Structure

```
.
├── backend/
│   ├── main.py                          # FastAPI app + CORS + lifespan handler
│   ├── gunicorn.conf.py                 # Gunicorn configuration
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tests/
│   ├── api/routes/
│   │   ├── vendors.py
│   │   ├── documents.py
│   │   ├── reviews.py
│   │   ├── decisions.py
│   │   └── audit.py
│   ├── core/
│   │   ├── config.py                    # Pydantic settings
│   │   ├── database.py                  # SQLAlchemy engine + session
│   │   └── models.py                    # ORM models + enums
│   ├── schemas/
│   │   ├── vendor.py
│   │   ├── document.py
│   │   ├── review.py
│   │   ├── decision.py
│   │   ├── audit.py
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
│       │   ├── legal_kb.py
│       │   ├── security_kb.py
│       │   └── loader.py                # seeds KB into ChromaDB on startup
│       ├── legal/analyzer.py            # Stage 2 AI module
│       └── security/analyzer.py         # Stage 3 AI module
├── frontend/
│   ├── Dockerfile                       # Multi-stage: node build → nginx serve
│   ├── nginx.conf                       # SPA routing + /api reverse proxy
│   ├── docker-entrypoint.sh
│   ├── package.json
│   ├── vite.config.ts                   # Dev proxy: /api → localhost:8000
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                      # Nav shell + routes
│       ├── api/client.ts                # Typed fetch wrappers
│       ├── types/index.ts               # TS interfaces mirroring backend schemas
│       ├── components/
│       │   ├── ui/                      # Badge, Button, Card, Spinner
│       │   ├── StatusStepper.tsx        # 6-step progress bar
│       │   ├── DocumentUpload.tsx
│       │   ├── DecisionPanel.tsx
│       │   ├── AuditTrail.tsx
│       │   └── ErrorBoundary.tsx
│       ├── pages/
│       │   ├── VendorListPage.tsx
│       │   └── VendorDetailPage.tsx
│       └── stages/
│           ├── UseCasePanel.tsx         # Stage 1 — human form
│           ├── LegalReviewPanel.tsx     # Stage 2 — AI report + decisions
│           ├── SecurityReviewPanel.tsx  # Stage 3 — AI report + NDA gate
│           └── FinancialPanel.tsx       # Stage 4 — human form
├── compose.yaml
└── .env.example
```
