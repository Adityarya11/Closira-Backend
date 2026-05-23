from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Followup(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enquiry_id: Mapped[int] = mapped_column(Integer, ForeignKey("enquiries.id"), nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    enquiry: Mapped["Enquiry"] = relationship("Enquiry", back_populates="followups")