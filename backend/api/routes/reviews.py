from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Review, Vendor
from schemas.forms import FinancialRiskFormInput, UseCaseFormInput
from schemas.review import ReviewRead

router = APIRouter()


@router.get("/vendors/{vendor_id}/reviews", response_model=list[ReviewRead])
def list_reviews(vendor_id: int, db: Session = Depends(get_db)):
    """List all reviews for a vendor across all stages."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return db.query(Review).filter(Review.vendor_id == vendor_id).all()


@router.get("/reviews/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Retrieve a single review by ID."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/reviews/{review_id}/trigger", response_model=ReviewRead)
def trigger_ai_review(review_id: int, doc_id: int, db: Session = Depends(get_db)):
    """
    Trigger AI analysis for a review (Stages 2 and 3).
    Requires a document ID to analyse.
    Implemented in Days 3 and 4.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    raise HTTPException(status_code=501, detail="Not implemented — coming Days 3/4")


@router.post("/reviews/{review_id}/submit-form", response_model=ReviewRead)
def submit_review_form(
    review_id: int,
    db: Session = Depends(get_db),
):
    """
    Submit a human form for Stage 1 (UseCaseFormInput) or Stage 4 (FinancialRiskFormInput).
    The request body must match the schema for the review's stage.
    Fully wired in Day 5.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    raise HTTPException(status_code=501, detail="Not implemented — coming Day 5")
