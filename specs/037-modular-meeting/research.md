# Phase 0 Research: Modular Meeting Sub-modules Architecture

**Feature Branch**: `037-modular-meeting`  
**Date**: 2026-10-31  

---

## 1. Technical Context & Baseline

- **Language / Runtime**: Python 3.12, FastAPI, Pydantic v2.
- **ORM & Database**: SQLAlchemy 2.0 (Mapped Columns, Declarative Base), PostgreSQL (TIMESTAMPTZ UTC).
- **Dependency Injection**: Dishka container (`providers.py`).
- **Codebase Pattern**: Clean Architecture / Practical DDD.
- **Current State**:
  - `meeting/domain/entity.py`: 292 lines (4 entities + value objects).
  - `meeting/schemas.py`: 517 lines (20+ DTOs).
  - `meeting/controller.py`: 551 lines (14+ route handlers).
  - `meeting/infrastructure/repository.py`: 828 lines (4 repository classes).
  - `meeting/application/`: Already decoupled into single-responsibility use case files.

---

## 2. Research Topics & Architectural Decisions

### Decision 1: Sub-Domain Decomposition Strategy

- **Context**: The `meeting` domain encompasses three distinct operational areas:
  1. *Core Meeting Lifecycle*: Scheduling, details, seat capacity, update, deletion.
  2. *Attendance & Check-in*: Self check-in, NFC/RFID Card check-in, checkout, admin status adjustments, batch check-in.
  3. *Meeting Evaluations*: Trainer rating trainee, trainee rating trainer, overall meeting feedback and metrics.
- **Decision**: Decompose all 4 monolithic layers (`domain`, `schemas`, `controllers`, `repositories`) along these 3 cohesive sub-domain pillars.
- **Rationale**:
  - Developers working on check-in/attendance won't touch evaluation queries or meeting CRUD.
  - Reduces file size from 500-800 lines to manageable 100-250 lines per file.
  - Matches the existing clean design seen in `homework` and `permission_request`.

---

### Decision 2: Circular Dependency Prevention in Domain Entities

- **Context**: `Meeting` aggregate root holds lists of `MeetingParticipant` and `MeetingEvaluation` / `MeetingOverallEvaluation`. Reciprocally, evaluations reference `meeting_id` and participants reference `meeting_id`.
- **Decision**:
  - Keep `EvaluationCriteria`, `EvaluationScoreItem`, `MeetingOverallEvaluation`, `MeetingEvaluation` in `domain/evaluation.py`.
  - Keep `MeetingParticipant` in `domain/participant.py`.
  - In `domain/meeting.py`, import `MeetingParticipant` and `MeetingOverallEvaluation` directly for type hints and relation lists.
  - Provide a barrel `domain/entity.py` (and `domain/__init__.py`) that re-exports all entities so external consumers (`homework`, `violation`, `permission_request`, `tests`) don't break.
- **Alternatives Considered**:
  - *Option A (Single giant file)*: Rejected by user request.
  - *Option B (Type comments/strings everywhere)*: Not needed; Python dataclasses/Pydantic cleanly resolve imports when DAG (Directed Acyclic Graph) order is respected:
    `evaluation.py` (independent) ➔ `participant.py` (independent) ➔ `meeting.py` (imports participant & evaluation).

---

### Decision 3: Router Composition in Presentation Layer

- **Context**: FastAPI needs a clean routing structure. If we split `controller.py` into sub-controllers, how should the top-level app mount them?
- **Decision**:
  - Create `app/meeting/controllers/`:
    - `meeting_controller.py`: router for core CRUD (`router = APIRouter()`).
    - `attendance_controller.py`: router for check-in/checkout/status.
    - `evaluation_controller.py`: router for evaluations and summaries.
  - In `app/meeting/controller.py` (root controller):
    ```python
    router = APIRouter(prefix="/meetings", tags=["meetings"])
    router.include_router(meeting_router)
    router.include_router(attendance_router)
    router.include_router(evaluation_router)
    ```
- **Rationale**:
  - Zero change to `app/main.py` or endpoint URLs.
  - Clean separation of endpoints by operational focus.
  - Controller files drop from 551 lines to ~120-180 lines each.

---

### Decision 4: Repository Package Structure

- **Context**: `infrastructure/repository.py` is 828 lines and has 4 repository classes with complex queries.
- **Decision**:
  - Create package `infrastructure/repositories/`:
    - `meeting_repository.py`: `MeetingRepository` (meeting queries, seat capacities, date filters).
    - `participant_repository.py`: `ParticipantRepository` (participant queries, status updates, check-in windows).
    - `meeting_evaluation_repository.py`: `MeetingEvaluationRepository` (trainee/trainer evaluation CRUD).
    - `meeting_overall_evaluation_repository.py`: `MeetingOverallEvaluationRepository` (overall evaluations).
    - `__init__.py`: Re-exports all 4 repository classes.
  - Maintain `infrastructure/repository.py` as a backward-compatible shim re-exporting from `infrastructure.repositories`.
- **Rationale**:
  - 100% compatibility with Dishka DI providers (`providers.py`).
  - Unit tests can mock or test individual repository files independently.

---

### Decision 5: Schemas Package Structure

- **Context**: `schemas.py` has 517 lines.
- **Decision**:
  - Create package `schemas/`:
    - `meeting_schemas.py`: `MeetingCreate`, `MeetingUpdate`, `MeetingResponse`, `MeetingDetailResponse`, `MeetingListQuery`, `UpcomingMeetingWithSeatsResponse`.
    - `participant_schemas.py`: `ParticipantResponse`, `UpdateParticipantStatusRequest`, `CheckInWithCardRequest`, `CheckInRequest`, `CheckInResponse`, `BatchCheckInRequest`.
    - `evaluation_schemas.py`: `EvaluationScoreItemDto`, `MeetingOverallEvaluationCreate`, `MeetingOverallEvaluationResponse`, `MeetingEvaluationCreate`, `EvaluationResponse`, `EvaluationSummaryResponse`, `MyEvaluationResponse`.
    - `__init__.py`: Re-exports all schemas via `__all__`.
- **Rationale**:
  - Callers can continue importing `from app.meeting.schemas import MeetingResponse` or import directly from sub-modules `from app.meeting.schemas.meeting_schemas import MeetingResponse`.
