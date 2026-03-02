"""
Development / demo utilities — NOT for production use.

POST /dev/seed
  Clears any existing vendor/document data and inserts three pre-defined
  mock vendors with THREE documents each (legal, security, financial),
  fully chunked and embedded into ChromaDB.  Calling this endpoint
  multiple times is safe (idempotent at the DB level — old rows are
  deleted before new ones are created).

Vendors seeded (9 documents total, 3 per vendor):
  1. Acme Analytics Inc.   — ✅ clean GDPR/PIPEDA privacy policy
                             ✅ SOC 2 Type II, recent pentest
                             ✅ healthy revenue growth, profitable
  2. DataFlow Inc.         — ⚠️ privacy policy: no intl-transfer mechanism,
                                no GDPR Art. 28 DPA language
                             ⚠️ security: pentest >18 months ago, no IR SLA
                             ⚠️ financial: declining revenue, high leverage,
                                going-concern note
  3. SecureVault Ltd.      — ⚠️ privacy policy: vague retention, no
                                sub-processor DPA clause
                             ❌ security questionnaire: no pentest, no IR SLA
                             ✅ financial: stable SaaS revenue, moderate leverage
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
            "SOC 2 Type II certified, healthy financials."
        ),
        "documents": [
            {
                "filename": "acme_analytics_privacy_policy.txt",
                "stage": DocumentStage.LEGAL,
                "doc_type": "privacy_policy",
            },
            {
                "filename": "acme_analytics_security_questionnaire.txt",
                "stage": DocumentStage.SECURITY,
                "doc_type": "security_questionnaire",
            },
            {
                "filename": "acme_analytics_financial_statement.txt",
                "stage": DocumentStage.FINANCIAL,
                "doc_type": "financial_statement",
            },
        ],
    },
    {
        "name": "DataFlow Inc.",
        "website": "https://dataflow.io",
        "description": (
            "Cloud data-integration platform — privacy policy has gaps, "
            "security posture below par, financial distress signals."
        ),
        "documents": [
            {
                "filename": "dataflow_privacy_policy.txt",
                "stage": DocumentStage.LEGAL,
                "doc_type": "privacy_policy",
            },
            {
                "filename": "dataflow_security_questionnaire.txt",
                "stage": DocumentStage.SECURITY,
                "doc_type": "security_questionnaire",
            },
            {
                "filename": "dataflow_financial_statement.txt",
                "stage": DocumentStage.FINANCIAL,
                "doc_type": "financial_statement",
            },
        ],
    },
    {
        "name": "SecureVault Ltd.",
        "website": "https://securevault.io",
        "description": (
            "UK document-management SaaS — ISO 27001 certified but no recent "
            "penetration test; privacy policy has DPA gaps; stable financials."
        ),
        "documents": [
            {
                "filename": "securevault_privacy_policy.txt",
                "stage": DocumentStage.LEGAL,
                "doc_type": "privacy_policy",
            },
            {
                "filename": "securevault_security_questionnaire.txt",
                "stage": DocumentStage.SECURITY,
                "doc_type": "security_questionnaire",
            },
            {
                "filename": "securevault_financial_statement.txt",
                "stage": DocumentStage.FINANCIAL,
                "doc_type": "financial_statement",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class SeededVendor(BaseModel):
    id: int
    name: str
    document_ids: list[int]
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
    Decisions, and AuditLogs), then creates three mock vendors with three
    documents each (legal, security, financial), fully chunked and embedded
    into ChromaDB.
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

        # 4. Create one Document per stage, chunk + embed each into ChromaDB.
        doc_ids: list[int] = []
        for doc_spec in spec["documents"]:
            mock_path = _MOCK_DIR / doc_spec["filename"]
            raw_text = mock_path.read_text(encoding="utf-8")

            document = Document(
                vendor_id=vendor.id,
                stage=doc_spec["stage"],
                doc_type=doc_spec["doc_type"],
                filename=doc_spec["filename"],
                raw_text=raw_text,
            )
            db.add(document)
            db.flush()  # populate document.id

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
            doc_ids.append(document.id)

        # 5. Create pending AI reviews for ALL three AI stages so every panel
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
                document_ids=doc_ids,
                review_id=use_case_review.id,
            )
        )

    db.commit()

    return SeedResponse(
        message=f"Seeded {len(seeded)} vendors with documents and pending reviews.",
        vendors=seeded,
    )
