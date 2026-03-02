from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import audit, decisions, documents, reviews, vendors
from services.knowledge_base.loader import KnowledgeBaseLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed knowledge base collections into ChromaDB (no-op after first run).
    # DB tables are created once in gunicorn's on_starting hook (gunicorn.conf.py)
    # to avoid a race condition when multiple workers start simultaneously.
    await KnowledgeBaseLoader().seed_if_empty()
    yield


app = FastAPI(
    title="GRC Vendor Onboarding API",
    description=(
        "AI-augmented vendor onboarding workflow for GRC automation. "
        "Supports four review stages: Use Case, Legal/Regulatory, Security Risk, "
        "and Financial Risk — with RAG-powered AI analysis for Stages 2 and 3."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
app.include_router(documents.router, tags=["documents"])
app.include_router(reviews.router, tags=["reviews"])
app.include_router(decisions.router, tags=["decisions"])
app.include_router(audit.router, tags=["audit"])


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
