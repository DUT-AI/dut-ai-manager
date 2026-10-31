# Implementation Plan: Modular Meeting Sub-modules Refactoring

**Branch**: `037-modular-meeting` | **Date**: 2026-10-31 | **Spec**: [specs/037-modular-meeting/spec.md](specs/037-modular-meeting/spec.md)

**Input**: User request: Refactor monolithic files (`repository.py`, `controller.py`, `schemas.py`, `entity.py`) in `backend/app/meeting/` into clean, maintainable sub-modules.

---

## Summary

The `meeting` domain currently houses four monolithic files totaling over 2,200 lines (`repository.py` ~828 lines, `controller.py` ~551 lines, `schemas.py` ~517 lines, `entity.py` ~292 lines). This plan outlines the systematic decomposition of these monolithic files into cohesive sub-modules aligned with the three core pillars of the meeting domain:
1. **Core Meeting Lifecycle** (Meetings CRUD, Seats, Capacity).
2. **Attendance & Check-in** (Self Check-in, RFID Card, Batch Check-in, Checkout, Attendance Status).
3. **Evaluations** (Trainer-Trainee Evaluation, Trainee-Trainer Evaluation, Overall Meeting Evaluation).

The refactoring will strictly preserve all external API route paths, JSON envelope contracts, Dishka DI wiring, and domain behaviors while reducing file sizes to manageable, single-responsibility units (100–250 lines each).

---

## Technical Context

- **Language/Version**: Python 3.12 (Strict typing, PEP 695 / PEP 585 generics).
- **Primary Dependencies**: FastAPI 0.115+, Pydantic v2.10+, SQLAlchemy 2.0 (Mapped columns), Dishka DI.
- **Storage**: PostgreSQL (TIMESTAMPTZ UTC, migration head `038_fix_participant_timestamptz`).
- **Testing**: `pytest`, `pytest-asyncio`, Starlette `TestClient`.
- **Target Platform**: Linux/macOS server backend, React/Vite web frontend, Zalo Mini App, ESP32 IoT clients.
- **Project Type**: Enterprise Web Service (REST API backend with Clean Architecture & DDD).
- **Performance Goals**: Zero performance regression, <50ms query execution on paginated meeting/participant queries.
- **Constraints**: 
  - Zero API route path changes.
  - 100% backward compatibility for internal imports via barrel re-exports (`__init__.py` and shim modules).
  - Strict absence of circular dependencies.

---

## Constitution Check

*GATE: Checked against DUT AI Manager Constitution v1.8.0. All gates PASSED.*

- **Principle I (Clean Architecture & Practical DDD Boundaries)**: **PASS**. Separates domain entities, application use cases, presentation controllers, and infrastructure repositories without cross-layer leaks.
- **Principle II (Dependency Injection with Dishka)**: **PASS**. All repositories maintain exact constructor signatures and continue to be bound and provided via `app/meeting/providers.py`.
- **Principle III (Enterprise UTC Storage & Vietnam Display Integrity)**: **PASS**. Retains TIMESTAMPTZ UTC storage and `UtcDateTime` / `IsoDateTime` serialization rules.
- **Principle V (API Backward Compatibility & Non-Null Contract DTOs)**: **PASS**. All endpoints maintain `/api/v1/meetings/*` paths and standardized `ApiResponse[T]` responses.
- **Principle VII (Strict Single-Responsibility Use Cases)**: **PASS**. Existing single-responsibility use cases in `app/meeting/application/` are preserved intact and merely import from the cleanly modularized repositories and entities.
- **Principle IX (Pure Composition Over Base Use Cases)**: **PASS**. No base use cases introduced; repositories and routers composed purely.
- **Principle X (Zero Redundant Backward Compatibility & No Duplicate API Surface)**: **PASS**. Internal shim files cleanly re-export canonical objects; no dual-named endpoint aliases or redundant wrappers created.
- **Principle XIII (Structured Generic Payload & Absolute Type Safety)**: **PASS**. Absolute static typing, explicit type casting with `app.utils.parsers`, no `dict[str, Any]` or `getattr()` dynamic workarounds.

---

## Project Structure

### Documentation (this feature)

```text
specs/037-modular-meeting/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output (meeting-api.md)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code Layout (backend/app/meeting/)

```text
backend/app/meeting/
├── domain/
│   ├── __init__.py                     # Barrel re-export of all domain models
│   ├── entity.py                       # Re-export shim for existing callers
│   ├── meeting.py                      # Meeting Aggregate Root & UpcomingMeetingWithSeats
│   ├── participant.py                  # MeetingParticipant Entity & business methods
│   ├── evaluation.py                   # MeetingEvaluation, MeetingOverallEvaluation, Criteria
│   ├── value_objects.py                # ParticipantStatus, EvaluationType
│   └── events.py                       # Domain Events (ParticipantCheckedIn, etc.)
│
├── schemas/
│   ├── __init__.py                     # Barrel re-export via __all__
│   ├── meeting_schemas.py              # MeetingCreate, Update, Response, Detail, Query
│   ├── participant_schemas.py          # ParticipantResponse, Status, Card, Batch DTOs
│   └── evaluation_schemas.py           # Evaluation Create, Response, Summary DTOs
│
├── controllers/
│   ├── __init__.py                     # Package init
│   ├── meeting_controller.py           # Core Meeting CRUD & upcoming seats routes
│   ├── attendance_controller.py        # Checkin, Card Checkin, Checkout, Status routes
│   └── evaluation_controller.py        # Trainer/Trainee/Overall Evaluation routes
│
├── controller.py                       # Root APIRouter mounting sub-routers
│
├── infrastructure/
│   ├── __init__.py
│   ├── model.py                        # SQLAlchemy ORM Models
│   ├── repository.py                   # Re-export shim for existing callers
│   └── repositories/
│       ├── __init__.py                 # Barrel re-export of all repositories
│       ├── meeting_repository.py       # MeetingRepository
│       ├── participant_repository.py   # ParticipantRepository
│       ├── meeting_evaluation_repository.py         # MeetingEvaluationRepository
│       └── meeting_overall_evaluation_repository.py # MeetingOverallEvaluationRepository
│
├── application/                        # Existing single-responsibility use cases
│   ├── ..._use_case.py
│   └── event_handlers.py
│
├── providers.py                        # Dishka DI provider configurations
└── deps.py                             # Dependency utilities
```

---

## Phases & Execution Strategy

### Phase 0: Outline & Research (Completed)
- Mapped all 2,200+ lines of monolithic code across the 4 targeted files.
- Verified DAG dependency graph to eliminate circular imports between `Meeting` and `MeetingParticipant` / `MeetingEvaluation`.
- Documented in `research.md`.

### Phase 1: Design & Contracts (Completed)
- Created entity-relationship class diagram and file allocation matrix in `data-model.md`.
- Documented full API endpoint routing matrix in `contracts/meeting-api.md`.
- Created end-to-end test verification procedure in `quickstart.md`.

### Phase 2: Implementation (via `/speckit-tasks` & `/speckit-implement`)
1. **Domain Layer Refactor**: Extract `domain/evaluation.py`, `domain/participant.py`, `domain/meeting.py`, and re-export via `domain/entity.py`.
2. **Infrastructure Repositories Refactor**: Extract `repositories/meeting_repository.py`, `repositories/participant_repository.py`, `repositories/meeting_evaluation_repository.py`, `repositories/meeting_overall_evaluation_repository.py`, and re-export via `infrastructure/repository.py`.
3. **Schemas Layer Refactor**: Create `schemas/meeting_schemas.py`, `schemas/participant_schemas.py`, `schemas/evaluation_schemas.py`, and re-export via `schemas/__init__.py`.
4. **Presentation Controllers Refactor**: Create `controllers/meeting_controller.py`, `controllers/attendance_controller.py`, `controllers/evaluation_controller.py`, and wire composite root router in `controller.py`.
5. **Quality Gates Verification**: Run Ruff lint checks, full pytest suite (`tests/unit/`, `tests/api/`), and frontend TypeScript compilation (`npm run build`).
