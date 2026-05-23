from fastapi import FastAPI
from app.core.config import settings
from app.core.database import Base, engine, check_db_connection
from app.models import enquiry, followup, timeline
from app.api.enquiry import router as enquiry_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="REST API backend for Closira's customer enquiry-handling pipeline.",
    version="1.0.0",
)

app.include_router(enquiry_router)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns API status and database connectivity.",
)
def health() -> dict:
    db_status = check_db_connection()
    return {
        "status": "ok",
        "database": "connected" if db_status else "unreachable",
    }