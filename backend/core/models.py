import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from core.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class VendorStatus(str, enum.Enum):
    INTAKE = "INTAKE"
    USE_CASE_REVIEW = "USE_CASE_REVIEW"
    USE_CASE_APPROVED = "USE_CASE_APPROVED"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    LEGAL_APPROVED = "LEGAL_APPROVED"
    NDA_PENDING = "NDA_PENDING"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    SECURITY_APPROVED = "SECURITY_APPROVED"
    FINANCIAL_REVIEW = "FINANCIAL_REVIEW"
    FINANCIAL_APPROVED = "FINANCIAL_APPROVED"
    ONBOARDED = "ONBOARDED"
    REJECTED = "REJECTED"


class DocumentStage(str, enum.Enum):
    USE_CASE = "USE_CASE"
    LEGAL = "LEGAL"
    SECURITY = "SECURITY"
    FINANCIAL = "FINANCIAL"


class ReviewType(str, enum.Enum):
    AI_ANALYSIS = "AI_ANALYSIS"
    HUMAN_FORM = "HUMAN_FORM"


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class DecisionAction(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(VendorStatus), default=VendorStatus.INTAKE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="vendor", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="vendor", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="vendor", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    stage = Column(Enum(DocumentStage), nullable=False)
    doc_type = Column(String(100), nullable=False)  # e.g. "SOC2", "privacy_policy"
    filename = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    chroma_collection_id = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    vendor = relationship("Vendor", back_populates="documents")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    stage = Column(Enum(DocumentStage), nullable=False)
    review_type = Column(Enum(ReviewType), nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    ai_output = Column(JSON, nullable=True)       # populated by AI analysis modules
    form_input = Column(JSON, nullable=True)      # populated by human form submissions
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    vendor = relationship("Vendor", back_populates="reviews")
    decisions = relationship("Decision", back_populates="review", cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    actor = Column(String(255), nullable=False)
    action = Column(Enum(DecisionAction), nullable=False)
    rationale = Column(Text, nullable=False)
    conditions = Column(JSON, nullable=True)      # list of condition strings, or null
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review = relationship("Review", back_populates="decisions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    vendor = relationship("Vendor", back_populates="audit_logs")
