1. BackgroundTasks over Celery — eliminates Redis/broker infra at the cost of
   no retry mechanism on task failure and no task queue persistence across restarts.

2. SQLite over PostgreSQL — zero setup, single file, sufficient for single-process
   evaluation workload. Does not support concurrent writes at scale.

3. Sync SQLAlchemy over async — avoids session lifecycle complexity that adds
   no real value at this workload size.

4. SOP matching is keyword heuristic only — first-match, no ranking, no NLP.
   Sufficient per assignment spec.

5. Follow-up scheduling is recorded but not executed — no APScheduler or cron.
   The scheduled_for timestamp is stored; actual delivery is out of scope.

6. No authentication — out of scope per assignment intent.

## Tech Stack

| Layer      | Choice                                            |
| ---------- | ------------------------------------------------- |
| Framework  | FastAPI                                           |
| ORM        | SQLAlchemy (sync, no async ORM complexity needed) |
| DB         | SQLite                                            |
| Async Work | FastAPI BackgroundTasks                           |
| Validation | Pydantic v2                                       |
| Logging    | Python `logging` + custom JSON formatter          |
| Server     | Uvicorn                                           |

## Database Schema — 3 Tables

**enquiries**

```
id              INTEGER PRIMARY KEY
customer_name   TEXT NOT NULL
channel         TEXT NOT NULL  -- whatsapp | email | call
message         TEXT NOT NULL
status          TEXT NOT NULL  -- OPEN | FOLLOWUP_SCHEDULED | ESCALATED | RESOLVED
matched_sop     TEXT           -- nullable until background task runs
suggested_response TEXT        -- nullable until background task runs
created_at      DATETIME
updated_at      DATETIME
```

**followups**

```
id               INTEGER PRIMARY KEY
enquiry_id       INTEGER FK → enquiries.id
delay_minutes    INTEGER NOT NULL
message_template TEXT
scheduled_for    DATETIME
created_at       DATETIME
```

**timelines**

```
id          INTEGER PRIMARY KEY
enquiry_id  INTEGER FK → enquiries.id
event_type  TEXT NOT NULL
message     TEXT
created_at  DATETIME
```

Timeline `event_type` values: `enquiry_created`, `sop_matched`, `sop_unmatched`, `followup_scheduled`, `escalated`, `response_generated`

---

## API Contract Summary

| Method | Endpoint                 | Status | Notes                                                   |
| ------ | ------------------------ | ------ | ------------------------------------------------------- |
| POST   | `/enquiry`               | 201    | Returns `enquiry_id` immediately, fires background task |
| POST   | `/enquiry/{id}/followup` | 200    | Validates enquiry not escalated                         |
| POST   | `/enquiry/{id}/escalate` | 200    | Accepts `reason`, updates status                        |
| GET    | `/enquiry/{id}/history`  | 200    | Returns enquiry + full timeline array                   |
| GET    | `/health`                | 200    | DB ping + status                                        |

---

## Background Task Flow

```
POST /enquiry received
        ↓
enquiry row created → status: OPEN
timeline event: enquiry_created
        ↓
BackgroundTask triggered (non-blocking)
        ↓
sop_matcher runs keyword match
        ↓
    match found?
    ├── YES → update matched_sop + suggested_response
    │          timeline: sop_matched, response_generated
    │          log: sop_matched
    └── NO  → status → ESCALATED
               timeline: sop_unmatched, escalated
               log: escalation_triggered
```

---

## SOP Dictionary (utils/sop_matcher.py)

5 SOPs, keyword-based, case-insensitive:

```
pricing     → ["price", "pricing", "cost", "rate", "charges", "fee"]
booking     → ["book", "appointment", "schedule", "slot", "reserve"]
complaint   → ["complaint", "issue", "problem", "bad", "unhappy", "refund"]
after_hours → ["closed", "after hours", "weekend", "holiday", "unavailable"]
general_info → ["info", "details", "tell me", "about", "how does", "what is"]
```

First match wins. No ranking needed for this scope.

---

## Error Handling Map

| Condition                     | HTTP Code                |
| ----------------------------- | ------------------------ |
| Enquiry not found             | 404                      |
| Invalid payload               | 422 (Pydantic auto)      |
| Followup on escalated enquiry | 400                      |
| Escalate already-escalated    | 400                      |
| DB error                      | 500 with generic message |

---
