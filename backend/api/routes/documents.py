from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Document, DocumentStage, Vendor
from schemas.document import DocumentRead
from services.document.chunker import DocumentChunker
from services.document.extractor import DocumentExtractor
from services.rag.store import VectorStore

router = APIRouter()


@router.post(
    "/vendors/{vendor_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    vendor_id: int,
    stage: DocumentStage,
    doc_type: str,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    """
    Upload a document for a vendor at a given workflow stage.
    Text extraction and chunking are implemented in Day 2.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    raw_text = DocumentExtractor().extract(file.file, file.filename or "")
    document = Document(
        vendor_id=vendor_id,
        stage=stage,
        doc_type=doc_type,
        filename=file.filename or "unknown",
        raw_text=raw_text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = DocumentChunker().chunk(raw_text, {"vendor_id": vendor_id, "stage": stage, "doc_id": document.id})
    collection = f"vendor_{vendor_id}_{stage.value}_{document.id}"
    VectorStore().upsert_chunks(collection, chunks)

    document.chroma_collection_id = collection
    db.commit()
    db.refresh(document)
    return document


@router.get("/vendors/{vendor_id}/documents", response_model=list[DocumentRead])
def list_documents(vendor_id: int, db: Session = Depends(get_db)):
    """List all documents uploaded for a vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return db.query(Document).filter(Document.vendor_id == vendor_id).all()


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Retrieve a single document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
