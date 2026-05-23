from typing import TypedDict


class SOP(TypedDict):
    keywords: list[str]
    response: str


SOPS: dict[str, SOP] = {
    "pricing": {
        "keywords": ["price", "pricing", "cost", "rate", "charges", "fee", "quote", "plan"],
        "response": "Thank you for your interest. Our pricing plans are tailored to your business needs. A representative will share a detailed quote with you shortly.",
    },
    "booking": {
        "keywords": ["book", "booking", "appointment", "schedule", "slot", "reserve", "availability"],
        "response": "We would be happy to schedule an appointment for you. Please share your preferred date and time and we will confirm the slot.",
    },
    "complaint": {
        "keywords": ["complaint", "issue", "problem", "bad", "unhappy", "refund", "wrong", "disappointed", "not working"],
        "response": "We sincerely apologise for the inconvenience. Your concern has been logged and a support agent will reach out to you within 24 hours.",
    },
    "after_hours": {
        "keywords": ["closed", "after hours", "weekend", "holiday", "unavailable", "off hours", "night"],
        "response": "Thank you for reaching out. Our team is currently unavailable but will respond to your enquiry on the next business day.",
    },
    "general_info": {
        "keywords": ["info", "information", "details", "tell me", "about", "how does", "what is", "explain"],
        "response": "Thank you for your enquiry. Our team will get back to you shortly with the relevant information.",
    },
}


def match_sop(message: str) -> tuple[str, str] | tuple[None, None]:
    normalised = message.lower()
    for sop_name, sop_data in SOPS.items():
        for keyword in sop_data["keywords"]:
            if keyword in normalised:
                return sop_name, sop_data["response"]
    return None, None