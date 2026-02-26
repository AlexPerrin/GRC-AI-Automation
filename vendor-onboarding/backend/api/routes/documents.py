from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Document, DocumentStage, Vendor
from schemas.document import DocumentRead

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

    # Day 2: extractor and chunker will process file.file here
    document = Document(
        vendor_id=vendor_id,
        stage=stage,
        doc_type=doc_type,
        filename=file.filename or "unknown",
    )
    db.add(document)
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
