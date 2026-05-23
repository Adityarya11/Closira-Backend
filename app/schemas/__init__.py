from .enquiry import EnquiryCreate, EnquiryDetail, EnquiryResponse
from .escalation import EscalationCreate, EscalationResponse
from .followup import FollowupCreate, FollowupResponse

# Backwards-compatible alias for older imports.
Escalate = EscalationCreate

__all__ = [
    "EnquiryCreate",
    "EnquiryDetail",
    "EnquiryResponse",
    "Escalate",
    "EscalationCreate",
    "EscalationResponse",
    "FollowupCreate",
    "FollowupResponse",
]
