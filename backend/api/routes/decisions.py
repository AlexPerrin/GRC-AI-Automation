from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Decision, Review
from schemas.decision import DecisionCreate, DecisionRead

router = APIRouter()


@router.post(
    "/reviews/{review_id}/decisions",
    response_model=DecisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_decision(
    review_id: int,
    payload: DecisionCreate,
    db: Session = Depends(get_db),
):
    """
    Record a human decision (APPROVE / REJECT / APPROVE_WITH_CONDITIONS) on a completed review.
    Workflow state transitions are wired in Day 5.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    decision = Decision(review_id=review_id, **payload.model_dump())
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.get("/reviews/{review_id}/decisions", response_model=list[DecisionRead])
def list_decisions(review_id: int, db: Session = Depends(get_db)):
    """List all decisions recorded against a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db.query(Decision).filter(Decision.review_id == review_id).all()
