from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from core.models import DecisionAction


class DecisionCreate(BaseModel):
    actor: str
    action: DecisionAction
    rationale: str
    conditions: Optional[List[str]] = None


class DecisionRead(BaseModel):
    id: int
    review_id: int
    actor: str
    action: DecisionAction
    rationale: str
    conditions: Optional[List[str]]
    decided_at: datetime

    model_config = {"from_attributes": True}
