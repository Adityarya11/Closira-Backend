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

5 SOPs, keyword-based, case-insensitive:# Closira Backend

REST API backend simulating Closira's customer enquiry-handling pipeline. Built with FastAPI, SQLite, and FastAPI BackgroundTasks.

---

## Stack

| Layer      | Choice                  |
| ---------- | ----------------------- |
| Framework  | FastAPI                 |
| ORM        | SQLAlchemy              |
| Validation | Pydantic v2             |
| Database   | SQLite                  |
| Async Work | FastAPI BackgroundTasks |
| Logging    | Python logging + JSON   |
| Server     | Uvicorn                 |

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Install and Run

```bash
git clone <repo-url>
cd closira-backend
uv sync
uv run uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint                 | Description                   |
| ------ | ------------------------ | ----------------------------- |
| POST   | `/enquiry`               | Create a new inbound enquiry  |
| POST   | `/enquiry/{id}/followup` | Schedule a follow-up          |
| POST   | `/enquiry/{id}/escalate` | Escalate to a human agent     |
| GET    | `/enquiry/{id}/history`  | Get full conversation history |
| GET    | `/health`                | API and database health check |

Full request/response examples are in `docs/api.http`.

---

## Database Schema

Three tables power the system.

### enquiries

Core entity. Holds the inbound message, channel, processing status, matched SOP, and suggested response.

```
id                 INTEGER PRIMARY KEY
customer_name      TEXT
channel            TEXT (whatsapp | email | call)
message            TEXT
status             TEXT (OPEN | FOLLOWUP_SCHEDULED | ESCALATED | RESOLVED)
matched_sop        TEXT (nullable)
suggested_response TEXT (nullable)
created_at         DATETIME
updated_at         DATETIME
```

### followups

Stores scheduled follow-up records. `scheduled_for` is computed from `delay_minutes` at creation time.

```
id                INTEGER PRIMARY KEY
enquiry_id        INTEGER FK → enquiries.id
delay_minutes     INTEGER
message_template  TEXT (nullable)
scheduled_for     DATETIME
created_at        DATETIME
```

### timelines

Append-only event log per enquiry. Powers the `/history` endpoint and gives the system a workflow-engine feel without additional infrastructure.

```
id          INTEGER PRIMARY KEY
enquiry_id  INTEGER FK → enquiries.id
event_type  TEXT
message     TEXT
created_at  DATETIME
```

Event types: `enquiry_created`, `sop_matched`, `sop_unmatched`, `response_generated`, `followup_scheduled`, `escalated`

SQLite was chosen to eliminate setup friction and keep the project runnable with a single command locally. In production, PostgreSQL would be preferred for concurrent writes, connection pooling, and stronger transactional guarantees.

---

## BackgroundTasks vs Celery

FastAPI BackgroundTasks was chosen intentionally over Celery for this assignment scope.

Celery introduces:

- A message broker (Redis or RabbitMQ) as a required infrastructure dependency
- Separate worker process management
- Additional operational complexity for monitoring and retries

For the current workload — lightweight SOP keyword matching triggered on enquiry creation — this overhead provides no meaningful benefit.

The tradeoff: BackgroundTasks runs in the same process as the API server. If the server restarts mid-task, the task is lost. There is no built-in retry mechanism. For production workloads involving heavy inference, guaranteed delivery, or distributed workers, Celery would be the correct choice.

---

## SOP Matching

Five hardcoded SOPs matched using case-insensitive keyword lookup against the inbound message. First match wins. If no SOP matches, the enquiry is automatically escalated and logged.

| SOP          | Example Keywords                       |
| ------------ | -------------------------------------- |
| pricing      | price, cost, rate, fee, quote          |
| booking      | book, appointment, schedule, slot      |
| complaint    | complaint, issue, refund, unhappy      |
| after_hours  | closed, weekend, holiday, after hours  |
| general_info | info, details, about, explain, what is |

---

## Async Workflow

```
POST /enquiry
     ↓
enquiry row created → status: OPEN
timeline event: enquiry_created
     ↓
BackgroundTask triggered (non-blocking, response returned immediately)
     ↓
keyword SOP matching runs
     ↓
match found → update matched_sop + suggested_response
              timeline: sop_matched, response_generated
no match    → status: ESCALATED
              timeline: sop_unmatched, escalated
```

---

## Structured Logging

All key events emit JSON logs to stdout.

```json
{"timestamp": "...", "level": "INFO", "event": "enquiry created", "logger": "...", "extra": {"enquiry_id": 1, "channel": "whatsapp", "event": "enquiry_created"}}
{"timestamp": "...", "level": "INFO", "event": "sop matched", "logger": "...", "extra": {"enquiry_id": 1, "matched_sop": "pricing", "event": "sop_matched"}}
{"timestamp": "...", "level": "WARNING", "event": "escalation triggered", "logger": "...", "extra": {"enquiry_id": 2, "reason": "no_sop_match", "event": "escalation_triggered"}}
```

---

## Error Handling

| Condition                               | Status |
| --------------------------------------- | ------ |
| Enquiry not found                       | 404    |
| Invalid or missing payload fields       | 422    |
| Follow-up on escalated enquiry          | 400    |
| Escalating an already-escalated enquiry | 400    |
| Database unreachable                    | 500    |

---

## Tradeoffs and Known Limitations

- **BackgroundTasks over Celery** — no retry on failure, task lost on server restart. Acceptable for assignment scope.
- **SQLite over PostgreSQL** — no concurrent write support. Sufficient for single-node local evaluation.
- **Sync SQLAlchemy** — avoids async session lifecycle complexity that adds no value at this scale.
- **SOP matching is keyword heuristic only** — first match wins, no ranking or NLP. Sufficient per assignment spec which explicitly excludes AI.
- **Follow-up execution is not implemented** — `scheduled_for` is stored but no scheduler executes the delivery. A production system would use APScheduler or a Celery beat task.
- **No authentication** — out of scope per assignment intent.
- **No tenant isolation** — schema supports future `tenant_id` column addition without restructuring.

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
