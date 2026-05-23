from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.enquiry import Enquiry
from app.models.timeline import Timeline
from app.schemas.enquiry import EnquiryCreate
from app.schemas.escalation import EscalationCreate
from app.core.logging import get_logger


logger = get_logger(__name__)


def create_enquiry(db: Session, payload: EnquiryCreate) -> Enquiry:
    enquiry = Enquiry(
        customer_name=payload.customer_name,
        channel=payload.channel,
        message=payload.message,
        status="OPEN",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    event = Timeline(
        enquiry_id=enquiry.id,
        event_type="enquiry_created",
        message=f"Enquiry received via {enquiry.channel} from {enquiry.customer_name}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()

    logger.info(
        "enquiry created",
        extra={"extra": {"enquiry_id": enquiry.id, "channel": enquiry.channel, "event": "enquiry_created"}},
    )

    return enquiry


def escalate_enquiry(db: Session, enquiry_id: int, payload: EscalationCreate) -> Enquiry:
    enquiry: Enquiry | None = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    if enquiry.status == "ESCALATED":
        raise HTTPException(status_code=400, detail="Enquiry is already escalated")

    enquiry.status = "ESCALATED"
    enquiry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enquiry)

    event = Timeline(
        enquiry_id=enquiry.id,
        event_type="escalated",
        message=f"Manually escalated. Reason: {payload.reason}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()

    logger.warning(
        "escalation triggered",
        extra={"extra": {"enquiry_id": enquiry_id, "reason": payload.reason, "event": "escalation_triggered"}},
    )

    return enquiry


def get_enquiry_history(db: Session, enquiry_id: int) -> dict:
    enquiry: Enquiry | None = (
        db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    )
    if not enquiry:
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    timeline = (
        db.query(Timeline)
        .filter(Timeline.enquiry_id == enquiry_id)
        .order_by(Timeline.created_at)
        .all()
    )

    return {
        "enquiry": enquiry,
        "timeline": timeline,
    }