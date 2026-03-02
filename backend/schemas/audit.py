from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    vendor_id: int
    event_type: str
    actor: str
    payload: Optional[Any]
    timestamp: datetime
    model_config = {"from_attributes": True}
