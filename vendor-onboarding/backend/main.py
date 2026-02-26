from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import decisions, documents, reviews, vendors
from core.database import Base, engine
from services.knowledge_base.loader import KnowledgeBaseLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all SQLite tables on startup (idempotent)
    Base.metadata.create_all(bind=engine)
    # Seed knowledge base collections into ChromaDB (no-op after first run)
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

app.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
app.include_router(documents.router, tags=["documents"])
app.include_router(reviews.router, tags=["reviews"])
app.include_router(decisions.router, tags=["decisions"])


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
