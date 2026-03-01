from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Vendor, VendorStatus
from schemas.vendor import VendorCreate, VendorList, VendorRead
from services.workflow import WorkflowService

router = APIRouter()


@router.post("/", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    """Create a new vendor and place it in INTAKE state."""
    vendor = Vendor(**payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/", response_model=VendorList)
def list_vendors(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all vendors with pagination."""
    vendors = db.query(Vendor).offset(skip).limit(limit).all()
    total = db.query(Vendor).count()
    return VendorList(vendors=vendors, total=total)


@router.get("/{vendor_id}", response_model=VendorRead)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """Retrieve a single vendor by ID."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/{vendor_id}/start-intake", response_model=VendorRead)
def start_intake(vendor_id: int, db: Session = Depends(get_db)):
    """Open Stage 1 Use Case review for a vendor in INTAKE status."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    try:
        vendor, _review = WorkflowService(db).create_vendor_and_intake(vendor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return vendor


@router.post("/{vendor_id}/confirm-nda", response_model=VendorRead)
def confirm_nda(vendor_id: int, db: Session = Depends(get_db)):
    """
    Confirm NDA execution for a vendor.
    Advances status from LEGAL_APPROVED -> SECURITY_REVIEW.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if vendor.status != VendorStatus.LEGAL_APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"NDA confirmation requires status LEGAL_APPROVED, current: {vendor.status}",
        )
    return WorkflowService(db).confirm_nda(vendor_id)


@router.post("/{vendor_id}/start-financial-review", response_model=VendorRead)
def start_financial_review(vendor_id: int, db: Session = Depends(get_db)):
    """Open Stage 4 Financial review for a vendor in SECURITY_APPROVED status."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    try:
        vendor, _review = WorkflowService(db).start_financial_review(vendor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return vendor


@router.post("/{vendor_id}/complete-onboarding", response_model=VendorRead)
def complete_onboarding(vendor_id: int, db: Session = Depends(get_db)):
    """Finalise vendor onboarding after all four stages are approved."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    try:
        return WorkflowService(db).complete_onboarding(vendor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{vendor_id}/reject", response_model=VendorRead)
def reject_vendor(vendor_id: int, rationale: str, db: Session = Depends(get_db)):
    """Reject a vendor at any stage."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    try:
        return WorkflowService(db).reject_vendor(vendor_id, stage="MANUAL", rationale=rationale)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
