"""
Shared test fixtures.

Strategy:
- Set DATABASE_URL to an in-memory SQLite URI before any app module is imported.
- Create a single StaticPool engine so every connection shares the same in-memory DB.
- Override FastAPI's get_db dependency to yield sessions from the test engine.
- _reset_db autouse fixture creates/drops tables; gunicorn on_starting hook handles
  production DB init so main.py no longer imports engine directly.
- Patch KnowledgeBaseLoader.seed_if_empty to a no-op so tests don't need ChromaDB.
"""
import os

# Must come before any app imports so pydantic-settings picks up the overrides.
os.environ["DATABASE_URL"] = "sqlite://"       # in-memory SQLite
os.environ.setdefault("LLM_PROVIDER_API_KEY", "test-key")
os.environ["CHROMA_HOST"] = ""                 # embedded mode; no server needed

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from core.database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# Shared test engine — StaticPool ensures all connections see the same DB.
# ---------------------------------------------------------------------------
_TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_db():
    """Create schema before each test and drop it afterwards for isolation."""
    Base.metadata.create_all(bind=_TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=_TEST_ENGINE)


@pytest.fixture
def db_session(_reset_db):
    """Yield a SQLAlchemy session bound to the test DB."""
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """
    Yield a FastAPI TestClient that:
      - uses the in-memory test DB (via get_db override)
      - runs the full app lifespan (tables already created by _reset_db)
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("main.KnowledgeBaseLoader.seed_if_empty", new_callable=AsyncMock):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
