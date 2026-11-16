# Tasks: System Architecture Redesign & Clean Architecture Blueprint (Homework Module)

**Input**: Design documents from `/specs/071-architecture-redesign/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/ports_contract.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- File paths are explicitly referenced in every task description.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline verification of existing test suites and codebase health before architectural refactor.

- [X] T001 Verify baseline test suites pass before refactoring by running `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py backend/tests/integration/test_homework_*.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Abstract Repository Ports definition in Domain layer. MUST be complete before adapting Repositories or Use Cases.

**⚠️ CRITICAL**: Foundational Ports must be defined and exported before implementing User Stories.

- [X] T002 Define `HomeworkRepositoryPort` in `backend/app/homework/domain/ports/homework_repository_port.py` per `specs/071-architecture-redesign/contracts/ports_contract.md`
- [X] T003 [P] Define `HomeworkSubmissionRepositoryPort` in `backend/app/homework/domain/ports/homework_submission_repository_port.py` per `specs/071-architecture-redesign/contracts/ports_contract.md`
- [X] T004 [P] Define `HomeworkAssigneeRepositoryPort` in `backend/app/homework/domain/ports/homework_assignee_repository_port.py` per `specs/071-architecture-redesign/contracts/ports_contract.md`
- [X] T005 Re-export all repository ports in `backend/app/homework/domain/ports/__init__.py` and `backend/app/homework/domain/__init__.py`

**Checkpoint**: Foundational Ports are ready and importable without circular dependencies.

---

## Phase 3: User Story 1 - Pure Domain Modeling & Zero-IO Business Logic (Priority: P1) 🎯 MVP

**Goal**: Verify that all core business logic (evaluating submissions, classifying statuses) executes within pure Domain Entities with zero dependencies on database or network.

**Independent Test**: Execute pure domain unit tests in < 1ms without any mocks or database connections.

### Implementation for User Story 1

- [X] T006 [US1] Create pure domain unit tests in `backend/tests/unit/test_homework_pure_domain.py` verifying `Homework.evaluate_submissions` and `Homework.index_submissions` execute in < 1ms with 0 mocks

**Checkpoint**: User Story 1 complete — Domain logic is 100% self-contained and independently verified.

---

## Phase 4: User Story 2 - Ports & Adapters with In-Memory Test Fixtures (Priority: P2)

**Goal**: Implement Hexagonal Architecture by attaching Ports to existing SQLAlchemy repositories and building In-Memory Fake Repositories to eradicate Mocking Hell.

**Independent Test**: Run contract test verifying both SQLAlchemy and In-Memory adapters conform 100% to Port interfaces.

### Implementation for User Story 2

- [X] T007 [P] [US2] Update `HomeworkRepository` in `backend/app/homework/infrastructure/homework_repository.py` to inherit from `HomeworkRepositoryPort`
- [X] T008 [P] [US2] Update `HomeworkSubmissionRepository` in `backend/app/homework/infrastructure/homework_submission_repository.py` to inherit from `HomeworkSubmissionRepositoryPort`
- [X] T009 [P] [US2] Update `HomeworkAssigneeRepository` in `backend/app/homework/infrastructure/homework_assignee_repository.py` to inherit from `HomeworkAssigneeRepositoryPort`
- [X] T010 [P] [US2] Create `InMemoryHomeworkRepository` in `backend/app/homework/infrastructure/in_memory/in_memory_homework_repo.py` per `specs/071-architecture-redesign/data-model.md`
- [X] T011 [P] [US2] Create `InMemoryHomeworkSubmissionRepository` in `backend/app/homework/infrastructure/in_memory/in_memory_submission_repo.py` per `specs/071-architecture-redesign/data-model.md`
- [X] T012 [P] [US2] Create `InMemoryHomeworkAssigneeRepository` in `backend/app/homework/infrastructure/in_memory/in_memory_assignee_repo.py` per `specs/071-architecture-redesign/data-model.md`
- [X] T013 [US2] Re-export in-memory repositories in `backend/app/homework/infrastructure/in_memory/__init__.py`
- [X] T014 [US2] Create contract test `backend/tests/unit/test_homework_ports_contract.py` verifying both SQLAlchemy and In-Memory adapters satisfy 100% of the Port contracts

**Checkpoint**: User Story 2 complete — Ports and Adapters established with interchangeable In-Memory fixtures.

---

## Phase 5: User Story 3 - Thin Orchestrator Use Cases & Zero-Mock Testing (Priority: P3)

**Goal**: Decouple Use Cases from concrete database implementations, inject Ports via Dishka, and build robust Zero-Mock tests using In-Memory repositories.

**Independent Test**: Execute Use Cases using In-Memory fixtures without any `MagicMock` for database repositories.

### Implementation for User Story 3

- [X] T015 [US3] Update Dishka provider in `backend/app/homework/providers.py` to provide repositories via Ports (`HomeworkRepositoryPort`, `HomeworkSubmissionRepositoryPort`, `HomeworkAssigneeRepositoryPort`)
- [X] T016 [US3] Update type annotations in Use Cases (`CheckOverdueHomeworkUseCase`, `GetUserHomeworkSubmissionsUseCase`, `RecordHomeworkSubmissionUseCase`) to depend on Ports
- [X] T017 [US3] Create Zero-Mock Use Case integration test suite `backend/tests/unit/test_homework_in_memory_use_cases.py` executing complete user flows against In-Memory repositories

**Checkpoint**: User Story 3 complete — Use Cases are completely decoupled from database mechanics and tested with real state in RAM.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: System-wide regression verification, code formatting, and quickstart scenarios validation.

- [X] T018 Run `backend/.venv/bin/ruff check backend/app/homework` and fix any formatting or import ordering issues
- [X] T019 Run full unit test suite `backend/.venv/bin/pytest backend/tests/unit/test_homework_*.py` and verify 100% tests pass
- [X] T020 Run full integration test suite `backend/.venv/bin/pytest backend/tests/integration/test_homework_*.py` and verify 100% tests pass
- [X] T021 Validate quickstart scenarios per `specs/071-architecture-redesign/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies — verifies baseline tests.
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks all user stories (defines abstract Ports).
- **User Story 1 (Phase 3)**: Can run immediately after Phase 2 (pure domain validation).
- **User Story 2 (Phase 4)**: Depends on Phase 2 — implements adapters for Ports.
- **User Story 3 (Phase 5)**: Depends on Phase 4 — wires Ports into DI and Use Cases, tested with In-Memory fakes.
- **Polish (Phase 6)**: Depends on completion of all stories (T001 to T017).

### Parallel Opportunities
- **Within Phase 2**: T003 [P] and T004 [P] can run alongside T002.
- **Within Phase 4 (US2)**: 
  - SQLAlchemy adapter updates (T007, T008, T009) can run in parallel.
  - In-Memory adapter implementations (T010, T011, T012) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 & Ports Foundation)
1. Complete Phase 1: Setup baseline check (T001)
2. Complete Phase 2: Foundational Ports (T002 - T005)
3. Complete Phase 3: Pure Domain Test (T006)
4. Validate: Domain rules run in < 1ms with 0 mocks.

### Incremental Delivery (Hexagonal & In-Memory)
1. Foundational Ports established.
2. Deliver US2: SQLAlchemy adapters inherit Ports, In-Memory repositories created, contract test verified.
3. Deliver US3: Dishka wiring and Zero-Mock use case tests.
4. Final Polish: Ruff clean, 100% regression tests PASS.
