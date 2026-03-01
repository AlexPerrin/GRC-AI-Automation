from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import DocumentStage, Review, ReviewType, Vendor
from schemas.forms import FinancialRiskFormInput, UseCaseFormInput
from schemas.review import ReviewRead
from services.workflow import WorkflowService

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
async def trigger_ai_review(review_id: int, doc_id: int, db: Session = Depends(get_db)):
    """
    Trigger AI analysis for a review (Stages 2 and 3).
    Requires a document ID to analyse.
    Stage 2 (LEGAL) implemented in Day 3; Stage 3 (SECURITY) in Day 4.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.review_type != ReviewType.AI_ANALYSIS:
        raise HTTPException(
            status_code=400,
            detail="This review is not an AI analysis review",
        )

    if review.stage == DocumentStage.LEGAL:
        return await WorkflowService(db).trigger_legal_review(review_id, doc_id)

    if review.stage == DocumentStage.SECURITY:
        try:
            return await WorkflowService(db).trigger_security_review(review_id, doc_id)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    raise HTTPException(status_code=501, detail="Not implemented — coming Day 5")


@router.post("/reviews/{review_id}/submit-form", response_model=ReviewRead)
def submit_review_form(
    review_id: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Submit a human form for Stage 1 (UseCaseFormInput) or Stage 4 (FinancialRiskFormInput).
    The request body must match the schema for the review's stage.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    svc = WorkflowService(db)
    try:
        if review.stage == DocumentStage.USE_CASE:
            form = UseCaseFormInput(**body)
            return svc.submit_use_case_form(review_id, form)
        elif review.stage == DocumentStage.FINANCIAL:
            form = FinancialRiskFormInput(**body)
            return svc.submit_financial_form(review_id, form)
        else:
            raise HTTPException(
                status_code=400,
                detail="This review stage does not accept form submissions",
            )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
