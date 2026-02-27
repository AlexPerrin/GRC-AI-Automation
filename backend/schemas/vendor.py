from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from core.models import VendorStatus


class VendorCreate(BaseModel):
    name: str
    website: Optional[str] = None
    description: Optional[str] = None


class VendorRead(BaseModel):
    id: int
    name: str
    website: Optional[str]
    description: Optional[str]
    status: VendorStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class VendorList(BaseModel):
    vendors: list[VendorRead]
    total: int
