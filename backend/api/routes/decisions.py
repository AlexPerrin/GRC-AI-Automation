from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Decision, DocumentStage, Review, ReviewStatus
from schemas.decision import DecisionCreate, DecisionRead
from services.workflow import WorkflowService

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
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status != ReviewStatus.COMPLETE:
        raise HTTPException(
            status_code=400,
            detail="Review must be COMPLETE before recording a decision",
        )

    decision = Decision(review_id=review_id, **payload.model_dump())
    db.add(decision)
    db.commit()
    db.refresh(decision)

    svc = WorkflowService(db)
    try:
        if review.stage == DocumentStage.LEGAL:
            svc.submit_legal_decision(
                review_id=review_id,
                action=payload.action.value,
                rationale=payload.rationale,
                conditions=payload.conditions,
                actor=payload.actor,
            )
        elif review.stage == DocumentStage.SECURITY:
            svc.submit_security_decision(
                review_id=review_id,
                action=payload.action.value,
                rationale=payload.rationale,
                conditions=payload.conditions,
                actor=payload.actor,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return decision


@router.get("/reviews/{review_id}/decisions", response_model=list[DecisionRead])
def list_decisions(review_id: int, db: Session = Depends(get_db)):
    """List all decisions recorded against a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db.query(Decision).filter(Decision.review_id == review_id).all()
