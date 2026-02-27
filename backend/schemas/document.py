from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from core.models import DocumentStage


class DocumentRead(BaseModel):
    id: int
    vendor_id: int
    stage: DocumentStage
    doc_type: str
    filename: str
    chroma_collection_id: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}
