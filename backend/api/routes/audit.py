from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import AuditLog, Vendor
from schemas.audit import AuditLogRead

router = APIRouter()


@router.get("/vendors/{vendor_id}/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.vendor_id == vendor_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return logs
