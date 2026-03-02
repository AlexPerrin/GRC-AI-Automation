"""
Development / demo utilities — NOT for production use.

POST /dev/seed
  Clears any existing vendor/document data and inserts three pre-defined
  mock vendors with their documents already chunked and embedded into
  ChromaDB.  Calling this endpoint multiple times is safe (idempotent
  at the DB level — old rows are deleted before new ones are created).

Vendors seeded:
  1. Acme Analytics Inc.   — clean GDPR/PIPEDA-compliant privacy policy
  2. DataFlow Inc.         — privacy policy with legal gaps (no intl-transfer
                             mechanism, no GDPR Art. 28 DPA language)
  3. SecureVault Ltd.      — security questionnaire with IR SLA gap and no
                             recent third-party penetration test evidence
"""
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import AuditLog, Decision, Document, DocumentStage, Review, ReviewStatus, ReviewType, Vendor, VendorStatus
from services.document.chunker import DocumentChunker
from services.rag.store import VectorStore

router = APIRouter(prefix="/dev", tags=["dev"])

# ---------------------------------------------------------------------------
# Paths to mock document files
# ---------------------------------------------------------------------------

_MOCK_DIR = Path(__file__).parent.parent.parent / "mock_data"

_VENDORS = [
    {
        "name": "Acme Analytics Inc.",
        "website": "https://acmeanalytics.io",
        "description": (
            "SaaS analytics vendor — strong GDPR/PIPEDA compliance, "
            "SOC 2 Type II certified, clean security posture."
        ),
        "document": {
            "filename": "acme_analytics_privacy_policy.txt",
            "stage": DocumentStage.LEGAL,
            "doc_type": "privacy_policy",
        },
    },
    {
        "name": "DataFlow Inc.",
        "website": "https://dataflow.io",
        "description": (
            "Cloud data-integration platform — privacy policy has gaps: "
            "no international transfer mechanism, no GDPR Art. 28 DPA language."
        ),
        "document": {
            "filename": "dataflow_privacy_policy.txt",
            "stage": DocumentStage.LEGAL,
            "doc_type": "privacy_policy",
        },
    },
    {
        "name": "SecureVault Ltd.",
        "website": "https://securevault.io",
        "description": (
            "UK document-management SaaS — ISO 27001 certified but no recent "
            "penetration test and no formal IR notification SLA."
        ),
        "document": {
            "filename": "securevault_security_questionnaire.txt",
            "stage": DocumentStage.SECURITY,
            "doc_type": "security_questionnaire",
        },
    },
]


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class SeededVendor(BaseModel):
    id: int
    name: str
    document_id: int
    review_id: int


class SeedResponse(BaseModel):
    message: str
    vendors: list[SeededVendor]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/seed", response_model=SeedResponse)
def seed_demo_data(db: Session = Depends(get_db)) -> SeedResponse:
    """
    Reset and re-seed demo data.

    Deletes all existing Vendor rows (cascades to Documents, Reviews,
    Decisions, and AuditLogs), then creates three mock vendors with one
    document each, fully chunked and embedded into ChromaDB.
    """
    # 1. Wipe existing data so repeated calls start from a clean state.
    #    Delete leaf tables first to avoid FK constraint failures on bulk delete.
    db.query(AuditLog).delete(synchronize_session=False)
    db.query(Decision).delete(synchronize_session=False)
    db.query(Review).delete(synchronize_session=False)
    db.query(Document).delete(synchronize_session=False)
    db.query(Vendor).delete(synchronize_session=False)
    db.commit()

    chunker = DocumentChunker()
    store = VectorStore()
    seeded: list[SeededVendor] = []

    for spec in _VENDORS:
        # 2. Create vendor record — immediately place in USE_CASE_REVIEW so the
        #    Use Case form tab is active when the demo opens.
        vendor = Vendor(
            name=spec["name"],
            website=spec["website"],
            description=spec["description"],
            status=VendorStatus.USE_CASE_REVIEW,
        )
        db.add(vendor)
        db.flush()  # populate vendor.id before creating children

        # 3. Create Stage 1 — Use Case review (human form, pending).
        #    This is what the frontend looks for to render the first tab.
        use_case_review = Review(
            vendor_id=vendor.id,
            stage=DocumentStage.USE_CASE,
            review_type=ReviewType.HUMAN_FORM,
            status=ReviewStatus.PENDING,
        )
        db.add(use_case_review)
        db.flush()

        doc_spec = spec["document"]
        mock_path = _MOCK_DIR / doc_spec["filename"]
        raw_text = mock_path.read_text(encoding="utf-8")

        # 4. Persist document record for the later AI stage (legal or security).
        document = Document(
            vendor_id=vendor.id,
            stage=doc_spec["stage"],
            doc_type=doc_spec["doc_type"],
            filename=doc_spec["filename"],
            raw_text=raw_text,
        )
        db.add(document)
        db.flush()  # populate document.id

        # 5. Chunk + embed into ChromaDB.
        collection = f"vendor_{vendor.id}_{doc_spec['stage'].value}_{document.id}"
        chunks = chunker.chunk(
            raw_text,
            {
                "vendor_id": vendor.id,
                "stage": doc_spec["stage"].value,
                "doc_id": document.id,
            },
        )
        store.upsert_chunks(collection, chunks)
        document.chroma_collection_id = collection

        # 6. Create pending AI reviews for ALL three AI stages so every panel
        #    always has a review record and can record decisions immediately.
        for stage in (DocumentStage.LEGAL, DocumentStage.SECURITY, DocumentStage.FINANCIAL):
            db.add(Review(
                vendor_id=vendor.id,
                stage=stage,
                review_type=ReviewType.AI_ANALYSIS,
                status=ReviewStatus.PENDING,
            ))
        db.flush()

        seeded.append(
            SeededVendor(
                id=vendor.id,
                name=vendor.name,
                document_id=document.id,
                review_id=use_case_review.id,
            )
        )

    db.commit()

    return SeedResponse(
        message=f"Seeded {len(seeded)} vendors with documents and pending reviews.",
        vendors=seeded,
    )
