# Tasks: Homework Constitution Hardening

**Input**: Design documents from `/specs/070-homework-constitution-hardening/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/homework_webhook_contract.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- File paths are explicitly referenced in every task description.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline verification of current test suites and environment health.

- [X] T001 Verify baseline test suites pass before refactoring by running `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py backend/tests/integration/test_homework_*.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Strongly-typed DTO definitions that MUST be created before updating Use Cases and Endpoints.

**⚠️ CRITICAL**: Foundational DTOs must be defined and exported before implementing User Stories.

- [X] T002 Define `HomeworkWebhookResponse` and update `HomeworkSubmissionWebhookIn` (`details: CodingSubmissionDetails | GameSubmissionDetails | None = None` with `model_validator`) in `backend/app/homework/application/dtos/submission_dtos.py` per `specs/070-homework-constitution-hardening/data-model.md`
- [X] T003 [P] Re-export `HomeworkWebhookResponse` in `backend/app/homework/application/dtos/__init__.py` and `backend/app/homework/application/__init__.py`

**Checkpoint**: Foundational DTOs are ready and importable across the application.

---

## Phase 3: User Story 1 - Strict Static Typing for Submission Details & Webhook (Priority: P1) 🎯 MVP

**Goal**: Webhook payload and submission DTOs enforce strict types (`CodingSubmissionDetails | GameSubmissionDetails`), eliminating raw `dict[str, Any]` in Webhook response/request, and removing `Any` in submission resolvers and status use cases.

**Independent Test**: Send webhook payload to `RecordHomeworkSubmissionUseCase.execute`, verify `HomeworkWebhookResponse` is returned. Verify `HomeworkExerciseResolver` and `GetHomeworkSubmissionStatusUseCase` compile with 0 `Any` types.

### Implementation for User Story 1

- [X] T004 [US1] Update `RecordHomeworkSubmissionUseCase.execute` in `backend/app/homework/application/record_submission_use_case.py` to return `HomeworkWebhookResponse` instead of raw `dict[str, Any]`
- [X] T005 [US1] Update webhook endpoint `/webhook/submission` in `backend/app/homework/controller.py` to use `response_model=ApiResponse[HomeworkWebhookResponse]` per `specs/070-homework-constitution-hardening/contracts/homework_webhook_contract.md`
- [X] T006 [P] [US1] Refactor `HomeworkExerciseResolver._extract_coding_exercises` in `backend/app/homework/application/homework_exercise_resolver.py` to accept `submissions: list[HomeworkSubmission]`, use direct property access (`sub.submission_type`, `sub.exercise_id`, `sub.exercise_title`), and remove `from typing import Any`
- [X] T007 [P] [US1] Refactor `GetHomeworkSubmissionStatusUseCase._evaluate_student` in `backend/app/homework/application/get_homework_submission_status_use_case.py` to type `db_exercise_map`, `db_coding_general_map`, `db_game_map` as `HomeworkSubmission` maps and remove `from typing import Any`
- [X] T008 [US1] Update integration test assertions in `backend/tests/integration/test_homework_webhook.py` to assert against `HomeworkWebhookResponse` fields and verify all webhook tests pass

**Checkpoint**: User Story 1 complete — Webhook flow and resolvers are 100% strictly typed with 0 `Any` and 0 raw dictionaries.

---

## Phase 4: User Story 2 - Remove Duck-Typing (`getattr`) on Domain Entities (Priority: P2)

**Goal**: Access domain entities strictly via declared contract fields, eliminating defensive `getattr(...)` duck-typing per Principle XIV & XIX.

**Independent Test**: Execute `GetUserHomeworkSubmissionsUseCase` and verify returned `HomeworkSubmissionDetailResponse` list matches domain entity fields using direct attribute access.

### Implementation for User Story 2

- [X] T009 [US2] Refactor `GetUserHomeworkSubmissionsUseCase.execute` in `backend/app/homework/application/get_user_homework_submissions_use_case.py` to access attributes directly (`s.exercise_id`, `s.exercise_title`, `s.score`, `s.attempt_number`, `s.created_at`) without `getattr`
- [X] T010 [US2] Refactor `HomeworkSubmissionDetailResponse.parse_typed_details` in `backend/app/homework/application/dtos/submission_dtos.py` to cleanly handle `HomeworkSubmission` domain entities via direct attribute access and remove duck-typing
- [X] T011 [US2] Run `backend/.venv/bin/pytest backend/tests/unit/test_homework_ssot.py` to ensure submission history extraction and evaluation operate cleanly without duck-typing

**Checkpoint**: User Story 2 complete — Domain entities are accessed exclusively via declared typed contracts.

---

## Phase 5: User Story 3 - Refactor Codebase to Reduce Complexity (C901) (Priority: P3)

**Goal**: Reduce cyclomatic complexity in `UpdateHomeworkUseCase.execute` and `HomeworkAssigneeRepository.sync_assignees` to <= 10, achieving 0 Ruff errors.

**Independent Test**: Run `backend/.venv/bin/ruff check backend/app/homework` and verify 0 errors / 0 warnings.

### Implementation for User Story 3

- [X] T012 [P] [US3] Refactor `UpdateHomeworkUseCase.execute` in `backend/app/homework/application/update_homework_use_case.py` by extracting private helpers `_validate_requirements` and `_sync_assignees_and_deadlines` to reduce complexity from 11 to <= 5
- [X] T013 [P] [US3] Refactor `HomeworkAssigneeRepository.sync_assignees` in `backend/app/homework/infrastructure/homework_assignee_repository.py` by extracting private helpers `_resolve_clean_deadline` and deadline update logic to reduce complexity from 11 to <= 6
- [X] T014 [US3] Run `backend/.venv/bin/ruff check backend/app/homework` to verify all C901 cyclomatic complexity errors are resolved

**Checkpoint**: User Story 3 complete — Codebase passes all Ruff linter checks with 0 errors.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: System-wide regression verification and documentation validation.

- [X] T015 Run full unit test suite `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py` and verify 100% tests pass
- [X] T016 Run full integration test suite `backend/.venv/bin/pytest backend/tests/integration/test_homework_*.py` and verify 100% tests pass
- [X] T017 Validate all quickstart verification scenarios per `specs/070-homework-constitution-hardening/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies — executes baseline test checks.
- **Foundational (Phase 2)**: Depends on T001 — blocks all user stories (defines DTOs).
- **User Story 1 (Phase 3)**: Depends on Phase 2 (T002, T003).
- **User Story 2 (Phase 4)**: Depends on Phase 2 (T002, T003) and can run in parallel with or after US1.
- **User Story 3 (Phase 5)**: Independent of US1/US2 implementation files; can run in parallel or after US1/US2.
- **Polish (Phase 6)**: Depends on completion of all user stories (T004 - T014).

### Parallel Opportunities
- **Within Phase 2**: T003 [P] can run alongside T002.
- **Within Phase 3 (US1)**: T006 [P] (`homework_exercise_resolver.py`) and T007 [P] (`get_homework_submission_status_use_case.py`) can run in parallel.
- **Within Phase 5 (US3)**: T012 [P] (`update_homework_use_case.py`) and T013 [P] (`homework_assignee_repository.py`) can run in parallel as they touch different files.

---

## Parallel Example: User Stories Execution

```bash
# Developer / Agent 1: User Story 1 (Webhook & Typing)
Task T004: "Update RecordHomeworkSubmissionUseCase.execute"
Task T005: "Update webhook endpoint in controller.py"
Task T006: "Refactor HomeworkExerciseResolver"
Task T007: "Refactor GetHomeworkSubmissionStatusUseCase"

# Developer / Agent 2: User Story 3 (C901 Complexity Refactor)
Task T012: "Refactor UpdateHomeworkUseCase.execute"
Task T013: "Refactor HomeworkAssigneeRepository.sync_assignees"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational DTOs (T002, T003)
3. Complete Phase 3: User Story 1 (T004 - T008)
4. **STOP and VALIDATE**: Run `pytest backend/tests/integration/test_homework_webhook.py` to confirm typed webhook handling.

### Incremental Delivery
1. Foundational DTOs established.
2. Deliver US1: Strict static typing & webhook DTOs (MVP).
3. Deliver US2: Remove duck-typing `getattr` on domain entities.
4. Deliver US3: Refactor C901 cyclomatic complexity.
5. Final Polish: Run complete test suite and linter checks.
