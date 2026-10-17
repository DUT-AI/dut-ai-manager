<!--
Sync Impact Report:
- Version: v1.4.0 -> v1.5.0
- Ratification Date: 2026-09-25
- Last Amended: 2026-10-18
- Principles enhanced / modified:
  - I. Clean Architecture & Practical DDD Boundaries (MUST) -> Clarified strict boundary between Repositories/Domain Services and Use Cases. Repositories handle data retrieval/persistence; Use Cases orchestrate business flows.
  - VII. Strict Single-Responsibility Use Cases (One Public Execute Per Class) (MUST) -> Strengthened enforcement: Each Use Case file MUST contain exactly ONE use case class with a single primary entrypoint method (`execute` or domain-specific action). Grouping multiple distinct queries/commands into a single use case class (e.g. `get_all`, `get_paged`, `get_assigned_to_user`, `get_unsubmitted_report` in one class) is strictly prohibited.
  - VIII. Frontend Component Modularity & Clean Hook Consumption (MUST) -> Mandated direct consumption of canonical hooks/services; prohibited redundant inline mutations, wrappers, or duplicate state logic.
  - IX. Pure Composition & Domain Services Over Base Use Cases (MUST) -> Maintained zero-base-use-case rule and explicit Dishka injection.
- Principles added:
  - X. Zero Redundant Backward Compatibility & No Duplicate API Surface (MUST) -> Strictly forbids creating duplicate aliases, dual-named functions/hooks, or obsolete compatibility layers that pollute the codebase (e.g., `useSyncHomework = useSyncHomeworkFromQuiz`). When renaming or refactoring, all call sites MUST be updated directly to use the canonical identifier.
- Rationale: Eliminating monolithic multi-method use cases, enforcing single responsibility across backend queries, and preventing codebase rot caused by needless backward compatibility aliases.
-->

# DUT AI Manager Constitution

## Core Principles

### I. Clean Architecture & Practical DDD Boundaries (MUST)
Every business domain in `dut-ai-manager` (Meeting, Homework, Violation, Report, User, PermissionRequest) MUST strictly follow Clean Architecture / Practical Domain-Driven Design layering:
- **Domain Layer (`domain/`)**: Pure business logic, Entities, Value Objects, and Domain Events. Must have ZERO dependencies on frameworks, databases, or third-party web APIs. May embed lightweight Value Objects (such as `UserRef(id, name, avatar_url)`) as identity snapshots for domain and use case cohesion.
- **Application Layer (`application/`)**: Dedicated Single-Responsibility Use Cases orchestrating domain logic, repositories, domain services, and domain event publishing.
- **Infrastructure Layer (`infrastructure/`)**: Database models (SQLAlchemy ORM), repositories, external service clients (MinIO, Discord, Zalo, Quiz). ORM Models MUST implement `to_entity()` and `from_entity()` methods for clean domain mapping. Raw database queries and multi-table filtering belong in Repositories, not in Use Cases or Controllers.
- **Presentation / API Layer (`controller.py`, `schemas.py`)**: FastAPI routers, Pydantic schemas, permission dependencies.

### II. Dependency Injection with Dishka (MUST)
All dependencies (Repositories, Use Cases, External Services) MUST be registered in Dishka providers (`providers.py`) and resolved using `@inject` with `FromDishka[...]` in FastAPI controllers or async job containers. Direct ad-hoc instantiation of services/repositories inside controllers or application logic is strictly forbidden.

### III. Unified UTC+7 Timezone & DateTime Integrity (MUST)
All business operations, attendance checks, deadline calculations, and cron jobs MUST operate on the **UTC+7 (Asia/Ho_Chi_Minh)** timezone. Code MUST use `app.utils.datetime.get_current_utc7_time()` or parse client ISO strings to naive UTC+7 before performing domain comparisons.

### IV. Event-Driven Decoupling & Asynchronous Handlers (MUST)
Side effects such as third-party notifications (Discord bot webhooks/messages, Zalo Mini App messages), audit logs, and real-time SSE broadcasts MUST be triggered asynchronously via `EventBus` (`DomainEvent` and `EventHandler`). Synchronous blocking calls to external notification APIs inside transaction paths are prohibited.

### V. API Backward Compatibility & Non-Null Contract DTOs (MUST)
Existing REST API endpoints consumed by the Web Frontend (`frontend/`) and Zalo Mini App (`zalo-mini-app/`) MUST maintain backward compatibility and follow the standardized envelope `ApiResponse[T]`. Read Model DTOs returned to client interfaces MUST enforce **Non-Null Contracts** for known relationships (e.g., `trainer: UserRefDto` must never be `undefined` or partial nulls), preventing fallback glitches on the frontend.

### VI. Idempotency & Network Resilience (MUST)
Any endpoint that records transactional state over unreliable networks (such as bulk check-in, card tap, check-out) MUST support idempotency keys (`client_event_id` / `event_id`) to prevent duplicate processing on client retries.

### VII. Strict Single-Responsibility Use Cases (One Public Execute Per Class) (MUST)
Each use case in the `application/` layer of every domain MUST strictly follow the Single-Responsibility Principle:
- **Dedicated File per Use Case**: Each use case MUST reside in its own dedicated Python file named `*_use_case.py` (e.g., `get_user_homeworks_use_case.py`, `get_unsubmitted_homeworks_use_case.py`, `sync_homework_submissions_use_case.py`).
- **Single Public Action**: Each use case class MUST expose exactly ONE primary public method (conventionally `execute(...)`). Bundling multiple unrelated read or write operations (e.g., bundling `get_all`, `get_paged`, `get_assigned_to_user`, `get_unsubmitted_report` inside a generic `GetHomeworksUseCase`) is strictly prohibited.
- **Export Discipline**: The domain's `application/__init__.py` file MUST explicitly re-export all use case classes via `__all__`.

### VIII. Frontend Component Modularity & Single-Responsibility UI (MUST)
All frontend features in `frontend/src/features/` MUST adhere to modular component architecture:
- **Strict Separation of Subcomponents**: Monolithic page or drawer files declaring multiple internal components (such as Modals, Form Modals, Tables, Mobile Lists, Timelines, Overview/Stats Cards) within a single file are strictly prohibited.
- **Dedicated Components Directory**: Subcomponents MUST be placed into individual files inside the feature's `components/` folder and exported cleanly via `components/index.ts`.
- **Orchestrator Role for Pages and Drawers**: Page and drawer components MUST act solely as orchestrators (managing query/mutation hooks, routing/modal visibility state, and top-level filter states), delegating presentation and table rendering to dedicated subcomponents.
- **Transparent Data Presentation & Pagination**: All data tables (`Table`) displaying business records MUST configure explicit pagination with `defaultPageSize >= 20`, `pageSizeOptions: ['10', '20', '50', '100']`, `showSizeChanger: true`, and `showTotal` indicators to guarantee no records are inadvertently clipped or hidden from administrators.

### IX. Pure Composition & Domain Services Over Base Use Cases (MUST)
Reusable business operations across use cases MUST be modeled as dedicated **Domain Services** (e.g. `TokenService`, `AuthService`, `AttendancePolicy`) or pure stateless utility functions:
- **Prohibition of Base Use Cases**: Creating generic/abstract "Base Use Case" classes (e.g., `BaseAuthUseCase`, `BaseMeetingUseCase`) solely to share helper methods or inject a bundle of common repositories is strictly prohibited. Use cases MUST maintain explicit, minimal dependencies in their `__init__`.
- **Favor Composition Over Inheritance**: Use cases requiring shared domain logic MUST either call stateless static methods on domain services (e.g. `TokenService.create_tokens(user)`) or inject the domain service directly via Dishka DI.
- **Independence & Modularity**: Each use case must remain self-contained, easily testable in isolation, and free from hidden coupling introduced by inheritance hierarchies.

### X. Zero Redundant Backward Compatibility & No Duplicate API Surface (MUST)
Both backend and frontend codebases MUST NOT retain redundant backward-compatibility layers, duplicate function aliases, or dual-named wrappers that pollute the codebase:
- **Prohibition of Internal Aliases**: Never create redundant re-exports or aliases (e.g., `export const useSyncHomework = useSyncHomeworkFromQuiz` or duplicate endpoints) merely to avoid updating callers.
- **Refactor Call Sites Directly**: When renaming, refactoring, or consolidating functions, hooks, DTOs, or services, all consuming callers MUST be updated directly to use the canonical identifier.
- **Single Source of Truth**: Every operation, endpoint, and hook MUST have exactly one canonical representation. Code cleanliness and maintainability strictly take precedence over lazy compatibility wrappers.

## Security & Compliance Standards

1. **Zero Secret Leakage**: No hardcoding of passwords, JWT secrets, Discord Bot tokens, MinIO credentials, or Zalo App secrets. All configurations MUST read from environment variables managed via `app.core.config.Settings`.
2. **Role-Based Access Control (RBAC)**: All administrative, modification, and deletion endpoints MUST enforce permission checks via `hasPermission(...)` and `CurrentUser`.
3. **Data Protection & Sanitization**: All file uploads MUST be validated for MIME type and stored in object storage (MinIO) with securely generated paths.

## Development Workflow & Quality Gates

1. **Test Verification**: Any change to domain entities, use cases, or critical calculations (e.g. Attendance 23:59 check, Capacity Monitor, Violation trigger) MUST be covered by automated unit/integration tests (`pytest`).
2. **Zero Regression Guarantee**: Changes to existing use cases MUST NOT break previously established test suites.
3. **Migration Integrity**: Database schema modifications MUST include corresponding Alembic migrations with reliable upgrade and downgrade paths.
4. **Production Build Validation**: Frontend refactorings MUST be validated via `npm run build` to verify zero TypeScript errors and bundle compilation health.

## Governance

1. **Constitution Authority**: This Constitution is the supreme design and architectural contract for `dut-ai-manager`. All specifications, implementation plans, and tasks generated via Spec Kit MUST comply with its principles.
2. **Amendments**: Amendments to these principles require explicit documentation, version bumping, and rationale justification.
3. **Versioning**: Semantic Versioning rules apply:
   - **MAJOR**: Breaking modifications to architectural boundaries or core principles.
   - **MINOR**: Addition of new principles or major workflow standards.
   - **PATCH**: Non-semantic clarifications and wording updates.

**Version**: 1.5.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-10-18
