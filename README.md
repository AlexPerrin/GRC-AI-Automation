# GRC-AI-Automation

AI-augmented vendor onboarding pipeline for Security Governance, Risk, and Compliance (GRC). Automates a four-stage due diligence workflow — Use Case, Legal/Regulatory, Security Risk, and Financial Risk — using RAG-powered LLM analysis with a human-in-the-loop approval flow and full audit trail.

**Stack:** FastAPI · Gunicorn (UvicornWorker) · SQLAlchemy / SQLite · ChromaDB · sentence-transformers · litellm

---

## Quickstart

```bash
git clone git@github.com:AlexPerrin/GRC-AI-Automation.git
cd GRC-AI-Automation
cp .env.example .env        # fill in LLM_PROVIDER_API_KEY
docker compose up --build
```

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ChromaDB | `http://localhost:8001` |

---

## Testing

Tests use an isolated in-memory SQLite database — no external services required.

```bash
# Ensure the stack is running
docker compose up -d

# Run the full suite
docker compose exec api python -m pytest tests/ -v

# Single module
docker compose exec api python -m pytest tests/test_api_vendors.py -v
```

| Module | Tests | Covers |
|---|---|---|
| `test_config.py` | 6 | `llm_model_string` for all providers, `chroma_use_server` toggle |
| `test_models.py` | 11 | ORM creation, FK relationships, cascade deletes, enum completeness |
| `test_schemas.py` | 15 | Pydantic validation — valid payloads, rejected values, required fields |
| `test_api_vendors.py` | 16 | Vendor CRUD, pagination, 404s, stub endpoints, health check |
| `test_llm_client.py` | 7 | JSON parsing, markdown fence stripping, invalid JSON error |
| **Total** | **57** | |

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

---

## API Overview

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

### Vendors

| Method | Path | Description |
|---|---|---|
| `POST` | `/vendors/` | Create a vendor (enters INTAKE state) |
| `GET` | `/vendors/` | List all vendors |
| `GET` | `/vendors/{id}` | Get vendor by ID |
| `POST` | `/vendors/{id}/confirm-nda` | Confirm NDA — advances LEGAL_APPROVED → SECURITY_REVIEW |
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

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## Project Structure

```
.
├── backend/
│   ├── main.py                          # FastAPI app + lifespan handler
│   ├── gunicorn.conf.py                 # Gunicorn configuration
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tests/
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
│       │   ├── legal_kb.py
│       │   ├── security_kb.py
│       │   └── loader.py                # seeds KB into ChromaDB on startup
│       ├── legal/analyzer.py            # Stage 2 AI module
│       └── security/analyzer.py         # Stage 3 AI module
├── .env.example
└── docker-compose.yml
```
