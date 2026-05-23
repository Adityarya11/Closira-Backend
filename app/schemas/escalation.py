from pydantic import BaseModel, Field


class EscalationCreate(BaseModel):
    reason: str = Field(..., min_length=1, examples=["Customer requested to speak with a human agent"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reason": "Customer requested to speak with a human agent",
                }
            ]
        }
    }


class EscalationResponse(BaseModel):
    enquiry_id: int
    status: str
    reason: str
    message: str