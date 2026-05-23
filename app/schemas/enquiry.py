
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class EnquiryCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100, examples=["John Doe"])
    channel: Literal["whatsapp", "email", "call"] = Field(..., examples=["whatsapp"])
    message: str = Field(..., min_length=1, examples=["I want to know the pricing details"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_name": "John Doe",
                    "channel": "whatsapp",
                    "message": "I want to know the pricing details",
                }
            ]
        }
    }


class EnquiryResponse(BaseModel):
    enquiry_id: int
    status: str
    message: str

    model_config = {"from_attributes": True}


class EnquiryDetail(BaseModel):
    id: int
    customer_name: str
    channel: str
    message: str
    status: str
    matched_sop: str | None
    suggested_response: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}