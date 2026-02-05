from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"
    TECHNICAL_SPEC = "technical_specification"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class RoutingDestination(str, Enum):
    HIGH_CONFIDENCE = "high_confidence_queue"
    MANUAL_REVIEW = "manual_review_queue"
    REJECTED = "rejected_queue"
    SPECIALIST_REVIEW = "specialist_review_queue"

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: ProcessingStatus
    message: str

class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float
    reasoning: str
    alternative_types: Optional[List[Dict[str, float]]] = None

class ExtractionResult(BaseModel):
    fields: Dict[str, Any]
    confidence: float
    extraction_method: str
    warnings: List[str] = []

class ValidationResult(BaseModel):
    is_valid: bool
    conflicts: List[Dict[str, Any]] = []
    missing_fields: List[str] = []
    confidence: float
    warnings: List[str] = []

class RoutingDecision(BaseModel):
    destination: RoutingDestination
    reasoning: str
    confidence: float
    requires_human_review: bool

class ProcessingResult(BaseModel):
    document_id: str
    status: ProcessingStatus
    classification: Optional[ClassificationResult] = None
    extraction: Optional[ExtractionResult] = None
    validation: Optional[ValidationResult] = None
    routing: Optional[RoutingDecision] = None
    processing_time: Optional[float] = None
    errors: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)