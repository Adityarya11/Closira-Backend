from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db, check_db_connection
from app.schemas.enquiry import EnquiryCreate, EnquiryResponse, EnquiryDetail
from app.schemas.followup import FollowupCreate, FollowupResponse
from app.schemas.escalation import EscalationCreate, EscalationResponse
from app.services.enquiry_service import create_enquiry, escalate_enquiry, get_enquiry_history
from app.services.followup_service import schedule_followup
from app.workers.background_tasks import process_enquiry


router = APIRouter(prefix="/enquiry", tags=["Enquiry"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EnquiryResponse,
    summary="Create a new inbound enquiry",
    description="Accepts a customer enquiry via WhatsApp, email, or call. Returns a job ID immediately and processes the enquiry asynchronously in the background.",
)
def create(
    payload: EnquiryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> EnquiryResponse:
    enquiry = create_enquiry(db, payload)
    background_tasks.add_task(process_enquiry, enquiry.id, db)
    return EnquiryResponse(
        enquiry_id=enquiry.id,
        status=enquiry.status,
        message="Enquiry received successfully",
    )


@router.post(
    "/{enquiry_id}/followup",
    status_code=status.HTTP_200_OK,
    response_model=FollowupResponse,
    summary="Schedule a follow-up for an enquiry",
    description="Schedules a follow-up for an open enquiry. Accepts a delay in minutes and an optional message template. Returns 400 if the enquiry is already escalated.",
)
def followup(
    enquiry_id: int,
    payload: FollowupCreate,
    db: Session = Depends(get_db),
) -> FollowupResponse:
    return schedule_followup(db, enquiry_id, payload)


@router.post(
    "/{enquiry_id}/escalate",
    status_code=status.HTTP_200_OK,
    response_model=EscalationResponse,
    summary="Escalate an enquiry to a human agent",
    description="Marks an enquiry as escalated. Accepts a reason field. Returns 400 if the enquiry is already escalated.",
)
def escalate(
    enquiry_id: int,
    payload: EscalationCreate,
    db: Session = Depends(get_db),
) -> EscalationResponse:
    enquiry = escalate_enquiry(db, enquiry_id, payload)
    return EscalationResponse(
        enquiry_id=enquiry.id,
        status=enquiry.status,
        reason=payload.reason,
        message="Enquiry escalated successfully",
    )


@router.get(
    "/{enquiry_id}/history",
    status_code=status.HTTP_200_OK,
    summary="Get full conversation history for an enquiry",
    description="Returns the enquiry details along with the complete status timeline ordered by time.",
)
def history(
    enquiry_id: int,
    db: Session = Depends(get_db),
) -> dict:
    data = get_enquiry_history(db, enquiry_id)
    enquiry = data["enquiry"]
    timeline = data["timeline"]

    return {
        "enquiry": {
            "id": enquiry.id,
            "customer_name": enquiry.customer_name,
            "channel": enquiry.channel,
            "message": enquiry.message,
            "status": enquiry.status,
            "matched_sop": enquiry.matched_sop,
            "suggested_response": enquiry.suggested_response,
            "created_at": enquiry.created_at.isoformat(),
            "updated_at": enquiry.updated_at.isoformat(),
        },
        "timeline": [
            {
                "event_type": event.event_type,
                "message": event.message,
                "timestamp": event.created_at.isoformat(),
            }
            for event in timeline
        ],
    }