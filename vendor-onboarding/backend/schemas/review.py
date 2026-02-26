from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from core.models import DocumentStage, ReviewStatus, ReviewType


class ReviewRead(BaseModel):
    id: int
    vendor_id: int
    stage: DocumentStage
    review_type: ReviewType
    status: ReviewStatus
    ai_output: Optional[Any]
    form_input: Optional[Any]
    triggered_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
