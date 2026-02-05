from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class DocumentState(TypedDict):
    document_id: str
    filename: str
    content: str
    metadata: Dict[str, Any]
    status: str
    classification_result: Optional[Dict[str, Any]]
    extraction_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    routing_decision: Optional[Dict[str, Any]]
    errors: List[str]
    start_time: datetime
    end_time: Optional[datetime]