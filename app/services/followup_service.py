from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.enquiry import Enquiry
from app.models.followup import Followup
from app.models.timeline import Timeline
from app.schemas.followup import FollowupCreate
from app.core.logging import get_logger


logger = get_logger(__name__)


def schedule_followup(db: Session, enquiry_id: int, payload: FollowupCreate) -> Followup:
    enquiry: Enquiry | None = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail=f"Enquiry {enquiry_id} not found")

    if enquiry.status == "ESCALATED":
        raise HTTPException(status_code=400, detail="Cannot schedule a follow-up for an escalated enquiry")

    scheduled_for = datetime.now(timezone.utc) + timedelta(minutes=payload.delay_minutes)

    followup = Followup(
        enquiry_id=enquiry_id,
        delay_minutes=payload.delay_minutes,
        message_template=payload.message_template,
        scheduled_for=scheduled_for,
        created_at=datetime.now(timezone.utc),
    )
    db.add(followup)

    enquiry.status = "FOLLOWUP_SCHEDULED"
    enquiry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(followup)

    event = Timeline(
        enquiry_id=enquiry_id,
        event_type="followup_scheduled",
        message=f"Follow-up scheduled for {scheduled_for.isoformat()} ({payload.delay_minutes} minutes from now)",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()

    logger.info(
        "followup scheduled",
        extra={"extra": {"enquiry_id": enquiry_id, "scheduled_for": scheduled_for.isoformat(), "event": "followup_scheduled"}},
    )

    return followup