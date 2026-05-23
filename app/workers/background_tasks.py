from sqlalchemy.orm import Session
from app.models.enquiry import Enquiry
from app.models.timeline import Timeline
from app.utils.sop_matcher import match_sop
from app.core.logging import get_logger
from datetime import datetime, timezone


logger = get_logger(__name__)


def _add_timeline_event(db: Session, enquiry_id: int, event_type: str, message: str) -> None:
    event = Timeline(
        enquiry_id=enquiry_id,
        event_type=event_type,
        message=message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()


def process_enquiry(enquiry_id: int, db: Session) -> None:
    logger.info(
        "task started",
        extra={"extra": {"enquiry_id": enquiry_id, "event": "task_started"}},
    )

    enquiry: Enquiry | None = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        logger.error(
            "enquiry not found in background task",
            extra={"extra": {"enquiry_id": enquiry_id}},
        )
        return

    matched_sop, suggested_response = match_sop(enquiry.message)

    if matched_sop:
        enquiry.matched_sop = matched_sop
        enquiry.suggested_response = suggested_response
        enquiry.updated_at = datetime.now(timezone.utc)
        db.commit()

        _add_timeline_event(
            db, enquiry_id, "sop_matched",
            f"Matched SOP: {matched_sop}",
        )
        _add_timeline_event(
            db, enquiry_id, "response_generated",
            f"Suggested response generated for SOP: {matched_sop}",
        )

        logger.info(
            "sop matched",
            extra={"extra": {"enquiry_id": enquiry_id, "matched_sop": matched_sop, "event": "sop_matched"}},
        )

    else:
        enquiry.status = "ESCALATED"
        enquiry.updated_at = datetime.now(timezone.utc)
        db.commit()

        _add_timeline_event(
            db, enquiry_id, "sop_unmatched",
            "No SOP matched for the inbound message",
        )
        _add_timeline_event(
            db, enquiry_id, "escalated",
            "Enquiry auto-escalated due to no SOP match",
        )

        logger.warning(
            "escalation triggered",
            extra={"extra": {"enquiry_id": enquiry_id, "event": "escalation_triggered", "reason": "no_sop_match"}},
        )