from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Timeline(Base):
    __tablename__ = "timelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enquiry_id: Mapped[int] = mapped_column(Integer, ForeignKey("enquiries.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    enquiry: Mapped["Enquiry"] = relationship("Enquiry", back_populates="timeline")