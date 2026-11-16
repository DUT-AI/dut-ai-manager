# Tasks: Full In-Memory Fake Test Migration for Homework Module

**Input**: Design documents from `/specs/072-homework-inmemory-test-migration/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/fixtures_contract.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- File paths are explicitly referenced in every task description.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline verification and creating shared in-memory test fixtures harness.

- [X] T001 Verify baseline test suites pass before migration by running `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py`
- [X] T002 Create shared in-memory fixtures in `backend/tests/fixtures/homework_fixtures.py` providing `in_memory_homework_repo`, `in_memory_submission_repo`, `in_memory_assignee_repo`, `fake_quiz_api`, and `spy_event_bus` per `specs/072-homework-inmemory-test-migration/contracts/fixtures_contract.md`
- [X] T003 Re-export shared fixtures in `backend/tests/conftest.py` so they are automatically discoverable by pytest across all test files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Enhance In-Memory Fake Repositories with test helper methods needed for expressive test assertions.

**⚠️ CRITICAL**: Must be completed before refactoring individual test files.

- [X] T004 Add test helper methods (e.g. `add_submissions`, `clear`) to `backend/app/homework/infrastructure/in_memory/in_memory_submission_repo.py`
- [X] T005 Add test helper methods (e.g. `clear`, state inspect) to `backend/app/homework/infrastructure/in_memory/in_memory_assignee_repo.py`
- [X] T006 [P] Verify shared fixture harness with a sanity test in `backend/tests/unit/test_homework_fixtures_sanity.py`

**Checkpoint**: Shared in-memory test harness ready and verified.

---

## Phase 3: User Story 1 - Migrate Checker & Scanner Test Suites to In-Memory Fakes (Priority: P1) 🎯 MVP

**Goal**: Refactor `test_homework_checker.py` and `test_homework_scanner.py` to run 100% on In-Memory Fake Repositories, removing all `MagicMock` for repositories.

**Independent Test**: `backend/.venv/bin/pytest backend/tests/unit/test_homework_checker.py backend/tests/unit/test_homework_scanner.py -v` passes 100% in < 0.2s with zero repository mocks.

### Implementation for User Story 1

- [X] T007 [US1] Refactor `test_check_overdue_homework_publishes_event` and `test_check_overdue_multi_exercise_partial_submission_flags_overdue` in `backend/tests/unit/test_homework_checker.py` to use `InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository`, `FakeQuizApiClient`, and `SpyEventBus`
- [X] T008 [US1] Refactor `test_check_overdue_multi_exercise_full_submission_passes` and `test_check_overdue_homework_default_target_date_delays_2_days` in `backend/tests/unit/test_homework_checker.py` to use In-Memory Fakes
- [X] T009 [US1] Refactor `test_check_overdue_homework_flags_late_submission` and `test_check_overdue_homework_per_assignee_independent_deadlines` in `backend/tests/unit/test_homework_checker.py` to use In-Memory Fakes
- [X] T010 [US1] Refactor `test_check_overdue_homework_uses_quiz_api_exercises` and `test_check_overdue_homework_fallbacks_when_quiz_api_fails` in `backend/tests/unit/test_homework_checker.py` to use In-Memory Fakes
- [X] T011 [US1] Remove all `MagicMock` and mock repository setups from `backend/tests/unit/test_homework_checker.py` and verify all 8 tests pass in < 0.2s
- [X] T012 [US1] Refactor `test_scanner_includes_partially_submitted_homework` in `backend/tests/unit/test_homework_scanner.py` to use In-Memory Fakes instead of `MagicMock(spec=HomeworkRepository)`

**Checkpoint**: User Story 1 complete — Checker and Scanner suites run 100% on RAM with Zero Mock repositories.

---

## Phase 4: User Story 2 - Migrate Validation & SSOT Test Suites to In-Memory Fakes (Priority: P2)

**Goal**: Refactor `test_homework_validation.py` and `test_homework_ssot.py` to use In-Memory Fakes for all repository operations.

**Independent Test**: `backend/.venv/bin/pytest backend/tests/unit/test_homework_validation.py backend/tests/unit/test_homework_ssot.py -v` passes 100% with real state verification in RAM.

### Implementation for User Story 2

- [X] T013 [P] [US2] Refactor homework creation tests (`test_create_homework_rejects_when_no_options_selected`, `test_create_homework_rejects_when_lesson_not_found_on_quiz`, `test_create_homework_rejects_when_coding_not_available`, `test_create_homework_rejects_when_game_not_available`, `test_create_homework_success`) in `backend/tests/unit/test_homework_validation.py` to use `InMemoryHomeworkRepository` and `InMemoryHomeworkAssigneeRepository`
- [X] T014 [US2] Refactor homework update and evaluation tests (`test_update_homework_validation`, `test_update_homework_uncheck_game_success`, `test_evaluate_submissions_partial_coding`, `test_evaluate_submissions_full_coding`) in `backend/tests/unit/test_homework_validation.py` to use In-Memory Fakes
- [X] T015 [US2] Remove all `MagicMock` for repositories from `backend/tests/unit/test_homework_validation.py`
- [X] T016 [P] [US2] Refactor `test_homework_extract_slug_and_effective_slug`, `test_homework_exercise_resolver_priority_and_fallback`, and `test_get_homework_submission_status_calculates_total_completed_count` in `backend/tests/unit/test_homework_ssot.py` to use In-Memory Fakes instead of `MagicMock` for repositories and submissions

**Checkpoint**: User Story 2 complete — Validation and SSOT suites run 100% on In-Memory Fakes.

---

## Phase 5: User Story 3 - Migrate Max Deadline Rule & Safe Deletion of Obsolete Mock Tests (Priority: P3)

**Goal**: Refactor the remaining mock test in `test_homework_max_deadline_rule.py`, clean up dead test code, and verify zero mock repository usage across all unit tests.

**Independent Test**: Quét `grep -rn "MagicMock" backend/tests/unit/test_homework_*.py | grep -E "repo|Repo"` trả về 0 kết quả; 100% tests PASS.

### Implementation for User Story 3

- [X] T017 [US3] Refactor Test Case 4 (`test_update_homework_use_case_protects_individual_deadlines`) in `backend/tests/unit/test_homework_max_deadline_rule.py` to use `InMemoryHomeworkRepository` and `InMemoryHomeworkAssigneeRepository`, verifying real deadline preservation in RAM instead of `assert_called_once_with`
- [X] T018 [US3] Clean up obsolete mock definitions, unused imports, and dead test helper code across `backend/tests/unit/test_homework_*.py`
- [X] T019 [US3] Audit codebase with `grep -rn "MagicMock" backend/tests/unit/test_homework_*.py` to verify zero `MagicMock` usage on `HomeworkRepository`, `HomeworkSubmissionRepository`, or `HomeworkAssigneeRepository`

**Checkpoint**: User Story 3 complete — All homework unit tests are 100% Zero-Mock for repositories.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: System-wide regression verification, code formatting, and quickstart scenarios validation.

- [X] T020 Run `backend/.venv/bin/ruff check backend/tests/unit/test_homework_*.py backend/tests/fixtures/` and fix any formatting or import ordering issues
- [X] T021 Run full unit test suite `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py -v` and verify 100% tests pass in < 1.5s
- [X] T022 Run full integration test suite `backend/.venv/bin/pytest backend/tests/integration/test_homework_*.py -v` and verify 100% tests pass
- [X] T023 Run full system test suite `backend/.venv/bin/pytest backend/tests/ -q` to guarantee 0 regressions across all 467+ tests
- [X] T024 Validate all 4 quickstart scenarios per `specs/072-homework-inmemory-test-migration/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Baseline test check and create shared fixture harness (`homework_fixtures.py`).
- **Foundational (Phase 2)**: Enhances In-Memory Fakes with helper methods. Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 — Refactors the largest and most complex mock file (`test_homework_checker.py` and `test_homework_scanner.py`).
- **User Story 2 (Phase 4)**: Depends on Phase 2 — Refactors validation and SSOT test suites.
- **User Story 3 (Phase 5)**: Depends on Phase 3 and Phase 4 — Refactors max deadline rule, cleans up obsolete mocks, audits zero-mock compliance.
- **Polish (Phase 6)**: Depends on completion of all stories (T001 to T019).

### Parallel Opportunities
- **Within Phase 1 & 2**: T006 can run in parallel with foundational fixture helpers.
- **Within Phase 4 (US2)**: T013 and T016 can run in parallel on different test files.
- **Cross-Story**: Once Phase 2 is complete, User Story 1 and User Story 2 can be developed independently.

---

## Implementation Strategy

### MVP First (User Story 1 - Checker Suite)
1. Complete Phase 1: Setup baseline check & shared fixtures (T001 - T003).
2. Complete Phase 2: Foundational fixture enhancements (T004 - T006).
3. Complete Phase 3: Deliver US1 — Refactor `test_homework_checker.py` and `test_homework_scanner.py`.
4. Validate: 8 checker tests + 1 scanner test run in < 0.2s with Zero Mock for repositories.

### Incremental Delivery
1. Foundational shared fixtures established.
2. Deliver US1: Checker & Scanner suites migrated to In-Memory Fakes (MVP).
3. Deliver US2: Validation & SSOT suites migrated to In-Memory Fakes.
4. Deliver US3: Max deadline rule migrated, obsolete mocks deleted, zero-mock audit verified.
5. Final Polish: Ruff clean, 100% full system regression tests PASS.
