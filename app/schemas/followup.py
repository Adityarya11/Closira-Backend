from datetime import datetime
from pydantic import BaseModel, Field


class FollowupCreate(BaseModel):
    delay_minutes: int = Field(..., gt=0, examples=[30])
    message_template: str | None = Field(None, examples=["Hi {name}, just following up on your enquiry."])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "delay_minutes": 30,
                    "message_template": "Hi {name}, just following up on your enquiry.",
                }
            ]
        }
    }


class FollowupResponse(BaseModel):
    id: int
    enquiry_id: int
    delay_minutes: int
    message_template: str | None
    scheduled_for: datetime
    created_at: datetime

    model_config = {"from_attributes": True}