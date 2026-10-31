# Feature Specification: Modular Sub-modules Refactoring for Meeting Domain

**Feature Branch**: `037-modular-meeting`  
**Created**: 2026-10-31  
**Status**: Ready for Planning  
**Input**: User request: Refactor monolithic files (`repository.py`, `controller.py`, `schemas.py`, `entity.py`) in `backend/app/meeting/` into clean, maintainable sub-modules.

---

## 1. Executive Summary & Problem Statement

Currently, the `backend/app/meeting/` domain contains four monolithic files with high cognitive load and mixed responsibilities:
1. `infrastructure/repository.py` (~828 lines): Bundles four distinct database repositories (`MeetingRepository`, `ParticipantRepository`, `MeetingEvaluationRepository`, `MeetingOverallEvaluationRepository`) together with complex multi-entity joins.
2. `controller.py` (~551 lines): Bundles 14+ endpoints spanning Meeting lifecycle CRUD, Attendance/Check-in/Checkout operations, and two-way Evaluation management into one massive router.
3. `schemas.py` (~517 lines): Contains 20+ request/response DTOs for Meetings, Participants, Card Check-in, Batch Operations, and Evaluations.
4. `domain/entity.py` (~292 lines): Houses multiple separate domain aggregates and entities (`Meeting`, `MeetingParticipant`, `MeetingEvaluation`, `MeetingOverallEvaluation`) along with evaluation criteria value objects.

### Refactoring Objectives
- **Sub-module Decomposition**: Group files logically by sub-domain capabilities:
  - **Core Meeting Lifecycle** (Meetings CRUD, Seats, Capacity).
  - **Attendance & Check-in** (Participants, Check-in with Card, Batch Check-in, Checkout, Attendance Status).
  - **Evaluations** (Trainer-Trainee Evaluation, Trainee-Trainer Evaluation, Overall Meeting Evaluation).
- **Clean Architecture & Constitution Compliance**: Comply with Constitution Principles I (Layering & DDD Boundaries), VII (Single-Responsibility), IX (Composition over monolithic classes), and X (Zero redundant backward-compatible bloat).
- **Zero API & Client Regressions**: Preserve all existing REST endpoint paths, request/response JSON contracts, and Dishka DI injection signatures. Ensure 100% of existing unit and API tests pass without degradation.

---

## 2. User Scenarios & Testing *(Prioritized)*

### User Story 1 - Clean Modular Repositories (Priority: P1)
As a Backend Engineer, I want distinct repository classes residing in dedicated files under `infrastructure/repositories/` so that database operations for Meetings, Participants, and Evaluations can be tested, maintained, and injected independently.

**Why this priority**: Repositories are the foundation of data access. Splitting the 828-line repository file clarifies query boundaries and prevents circular dependencies.

**Independent Test**:
- Can run unit tests for `MeetingRepository`, `ParticipantRepository`, `MeetingEvaluationRepository`, and `MeetingOverallEvaluationRepository` in isolation.
- Dishka container registers and injects each repository cleanly without circular import issues.

**Acceptance Scenarios**:
1. **Given** a query for meeting details, **When** `MeetingRepository.get_by_id(id)` is called, **Then** it returns the `Meeting` entity with relations loaded as before.
2. **Given** an attendance status update, **When** `ParticipantRepository.update_participant_status(...)` is called, **Then** it executes without touching evaluation queries.

---

### User Story 2 - Modular Domain Entities & Value Objects (Priority: P1)
As a Domain Developer, I want domain entities to be separated into dedicated domain files (`meeting.py`, `participant.py`, `evaluation.py`) so that domain invariants, attendance state transitions, and evaluation rules can be evolved without file collision.

**Why this priority**: Domain entities embody core business rules (e.g. check-in timestamp rules, evaluation score averages).

**Independent Test**:
- Domain unit tests (`test_meeting_domain.py`, `test_meeting_use_cases.py`) run with zero schema or framework dependencies.

**Acceptance Scenarios**:
1. **Given** a `MeetingParticipant`, **When** `update_attendance_status(JOINED)` is invoked, **Then** Option A business logic sets `check_in_at` to `meeting.start_time` seamlessly.
2. **Given** evaluation criteria and scores, **When** calculating `average_score` in `MeetingOverallEvaluation`, **Then** the value object computes the exact float average.

---

### User Story 3 - Modular Schemas & DTO Contracts (Priority: P2)
As an API Developer, I want request/response schemas partitioned into `meeting_schemas.py`, `participant_schemas.py`, and `evaluation_schemas.py` with seamless barrel re-exports from `schemas/` so that importing DTOs is clean, type-safe, and backward-compatible for all use cases.

**Why this priority**: Avoids maintaining a 500+ line schema file where unrelated changes cause git merge conflicts.

**Independent Test**:
- Importing from `app.meeting.schemas` or sub-schema files compiles with zero Pydantic validation errors.

**Acceptance Scenarios**:
1. **Given** a meeting creation request, **When** validated by `MeetingCreate`, **Then** UTC normalization and date validation function identically.
2. **Given** a participant response, **When** serialized via `ParticipantResponse`, **Then** TIMESTAMPTZ UTC strings with `Z` suffix are preserved.

---

### User Story 4 - Modular API Controllers & Routers (Priority: P2)
As a Frontend/Mobile Client, I want all `/api/v1/meetings/*` endpoints to remain completely unchanged in URL path and JSON envelope, while the backend organizes route handlers into dedicated controllers (`meeting_controller.py`, `attendance_controller.py`, `evaluation_controller.py`).

**Why this priority**: Guarantees zero regression for the Web frontend, Zalo Mini App, and ESP32 check-in devices.

**Independent Test**:
- `test_meeting_api.py` and `test_change_meeting_api.py` run against the composite router with all endpoints responding with exact HTTP status codes and payloads.

**Acceptance Scenarios**:
1. **Given** an ESP32 or card reader request to `POST /api/v1/meetings/check-in-with-card`, **When** processed by `attendance_controller`, **Then** it returns the exact audio stream and headers as before.
2. **Given** a Trainer submitting an evaluation to `POST /api/v1/meetings/{id}/trainer-evaluations`, **When** processed by `evaluation_controller`, **Then** permissions and event dispatching work without regression.

---

## 3. Requirements

### Functional Requirements
- **FR-001**: System MUST partition `backend/app/meeting/domain/entity.py` into:
  - `domain/meeting.py`: `Meeting` aggregate root and `UpcomingMeetingWithSeats`.
  - `domain/participant.py`: `MeetingParticipant`.
  - `domain/evaluation.py`: `MeetingEvaluation`, `MeetingOverallEvaluation`, `EvaluationScoreItem`, `EvaluationCriteria`.
  - `domain/entity.py` (or `domain/__init__.py`): Re-exports all domain entities and types.
- **FR-002**: System MUST partition `backend/app/meeting/infrastructure/repository.py` into:
  - `infrastructure/repositories/meeting_repository.py`: `MeetingRepository`.
  - `infrastructure/repositories/participant_repository.py`: `ParticipantRepository`.
  - `infrastructure/repositories/meeting_evaluation_repository.py`: `MeetingEvaluationRepository`.
  - `infrastructure/repositories/meeting_overall_evaluation_repository.py`: `MeetingOverallEvaluationRepository`.
  - `infrastructure/repository.py` and `infrastructure/repositories/__init__.py`: Re-exports all repositories.
- **FR-003**: System MUST partition `backend/app/meeting/schemas.py` into:
  - `schemas/meeting_schemas.py`: Meeting CRUD DTOs and filters.
  - `schemas/participant_schemas.py`: Attendance, Check-in, Card, and Batch DTOs.
  - `schemas/evaluation_schemas.py`: Evaluation and Summary DTOs.
  - `schemas/__init__.py`: Re-exports all schemas with `__all__`.
- **FR-004**: System MUST partition `backend/app/meeting/controller.py` into:
  - `controllers/meeting_controller.py`: Core meeting endpoints (`/`, `/{id}`, `/upcoming-with-seats`).
  - `controllers/attendance_controller.py`: Check-in, Card, Checkout, Participant status, Batch check-in.
  - `controllers/evaluation_controller.py`: Trainer, Trainee, Overall evaluations, and summaries.
  - `controller.py`: Root composite router mounting sub-routers under `/meetings`.
- **FR-005**: Dishka DI providers (`app/meeting/providers.py`) MUST resolve all repository and use case dependencies without breakage.
- **FR-006**: All existing unit tests (`tests/unit/test_meeting_*.py`) and API tests (`tests/api/test_meeting_api.py`) MUST pass 100%.

---

## 4. Edge Cases & Constraints

- **Circular Imports**: Domain entities (`Meeting` references `MeetingParticipant` and `MeetingOverallEvaluation`). Cross-references must use clean typing imports (`from typing import TYPE_CHECKING`) or careful ordering to guarantee zero circular dependency cycles.
- **Backward Compatibility of Imports**: Internal application use cases and tests currently import from `app.meeting.domain.entity`, `app.meeting.schemas`, and `app.meeting.infrastructure.repository`. The modular re-export files MUST maintain complete compatibility for all existing import statements.
- **Router Prefix Cohesion**: Sub-routers must use relative routes so that mounting under the main `/meetings` router preserves exact URLs:
  - `POST /meetings/check-in-with-card`
  - `PUT /meetings/{meeting_id}/participants/{user_id}/status`
  - `POST /meetings/{meeting_id}/trainer-evaluations`
