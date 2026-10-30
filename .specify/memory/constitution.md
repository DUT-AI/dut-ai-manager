<!--
Sync Impact Report:
- Version: v1.7.0 -> v1.8.0
- Ratification Date: 2026-09-25
- Last Amended: 2026-10-31
- Principles enhanced / added:
  - XIII. Structured Generic Payload & Absolute Type Safety (MUST) -> Strict ban on `dict[str, Any]`, `getattr()`, and loose `# type: ignore`. When modeling polymorphic entities (e.g., PermissionRequest), specialized data MUST use structured JSON payload mapped to immutable Pydantic Discriminated Unions. Type parsing from DB/JSON to Domain Entities MUST be explicit and safe via centralized utilities (`parse_datetime`, `parse_int`). Mandatory dependencies in Use Cases and Strategies MUST be required parameters and MUST NOT be default-initialized to `None = None`.
  - X. Zero Redundant Backward Compatibility & No Duplicate API Surface (ENHANCED) -> Explicitly mandate immediate deprecation and deletion of legacy sparse database columns and fallback logic during refactoring. Migration backfill must be performed immediately, legacy columns dropped from database schemas, and all consumer call-sites refactored directly to the canonical API.
- Rationale: Codifying enterprise-grade type safety, polymorphic strategy payloads, and zero-tolerance legacy column cleanup across all domain models and application use cases.
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

### III. Enterprise UTC Storage & Vietnam Display Integrity (MUST)
All backend models, domain entities, background jobs, and database tables MUST store, process, and compare timestamps using **Timezone-Aware UTC** (`datetime.now(timezone.utc)` and `DateTime(timezone=True)` / `TIMESTAMPTZ`).
- **Zero Naive Datetimes**: Naive datetime usage is strictly prohibited across application code and enforced via the Ruff `DTZ` linter.
- **Client Ingestion**: Inbound API requests accept naive or aware strings. Naive inputs are interpreted as Vietnam local time (`Asia/Ho_Chi_Minh`, UTC+7) and normalized into timezone-aware UTC via `UtcDateTime` DTOs (`app.shared.domain.datetime_types`).
- **Date/Month Calculations**: Periodic jobs and daily scheduling querying local days/months MUST explicitly project from UTC to Vietnam timezone: `datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()`.
- **Display Layer**: Dates are returned in ISO 8601 UTC or formatted to `Asia/Ho_Chi_Minh` on client interfaces and notification channels.

### IV. Event-Driven Decoupling & Asynchronous Handlers (MUST)
Side effects such as third-party notifications (Discord bot webhooks/messages, Zalo Mini App messages), audit logs, and real-time SSE broadcasts MUST be triggered asynchronously via `EventBus` (`DomainEvent` and `EventHandler`). Synchronous blocking calls to external notification APIs inside transaction paths are prohibited.

### V. API Backward Compatibility & Non-Null Contract DTOs (MUST)
Existing REST API endpoints consumed by the Web Frontend (`frontend/`) and Zalo Mini App (`zalo-mini-app/`) MUST maintain backward compatibility and follow the standardized envelope `ApiResponse[T]`. Read Model DTOs returned to client interfaces MUST enforce **Non-Null Contracts** for known relationships (e.g., `trainer: UserRefDto` must never be `undefined` or partial nulls), preventing fallback glitches on the frontend.

### VI. Idempotency & Network Resilience (MUST)
Any endpoint that records transactional state over unreliable networks (such as bulk check-in, card tap, check-out) MUST support idempotency keys (`client_event_id` / `event_id`) to prevent duplicate processing on client retries.

### VII. Strict Single-Responsibility Use Cases (One Public Execute Per Class) (MUST)
Each use case in the `application/` layer of every domain MUST strictly follow the Single-Responsibility Principle:
- **Dedicated File per Use Case**: Each use case MUST reside in its own dedicated Python file named `*_use_case.py` (e.g., `get_user_homeworks_use_case.py`, `get_unsubmitted_homeworks_use_case.py`, `sync_homework_submissions_use_case.py`).
- **Single Public Action**: Each use case class MUST expose exactly ONE primary public method (conventionally `execute(...)`). Bundling multiple unrelated read or write operations inside a generic class is strictly prohibited.
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
- **Immediate Removal of Legacy Columns**: When migrating database fields to consolidated structures (e.g., shifting metadata columns into JSON payloads), legacy sparse columns and their foreign key constraints MUST be promptly backfilled and dropped via migrations. Never maintain dual-write or sparse legacy columns out of hesitation to refactor.
- **Single Source of Truth**: Every operation, endpoint, and hook MUST have exactly one canonical representation. Code cleanliness and maintainability strictly take precedence over lazy compatibility wrappers.

### XI. Plain Text Notifications & Clean Channel Presentation (MUST)
All notification messages dispatched across channels (`Zalo Bot`, `Discord Bot/Embeds`, `In-App Notifications`, `Web Push`) MUST be formatted as clean plain text:
- **Strict Prohibition of Raw Markdown**: Raw markdown formatting symbols such as `**bold**`, `*italic*`, `` `inline_code` ``, and `[label](url)` are strictly forbidden in `NotificationPayload` titles, content, and field values. Channels like Zalo Bot and Web In-App modals display raw text literally, making markdown tokens appear cluttered and unpolished.
- **Visual Structure & Emoji Hierarchy**: Visual readability MUST be achieved through structured line breaks (`\n`), bullet points (`•`), capitalized category headings, and standard emojis (`📢`, `⏰`, `👤`, `📅`, `👉`, `•`, `⚠️`).
- **Direct Navigation Links**: Actionable links MUST be specified via the dedicated `action_url` payload attribute or rendered as plain URLs prefixed with descriptive action labels (e.g. `👉 Xem chi tiết tại: {url}`).

### XII. Server-Driven Filtering & Pagination Cohesion (MUST)
All data-listing views (tables, cards, virtual lists) backed by server-side pagination (`LIMIT/OFFSET` or cursor-based) MUST strictly delegate filtering to the backend:
- **Prohibition of Hybrid/Client-Side Filtering on Server Pages**: Client-side filtering (e.g., `items.filter(...)` via `useMemo` over paginated query responses) is strictly forbidden when server pagination is active. Filtering on a pre-paginated subset results in missing rows on earlier pages and fragmented pagination counts.
- **Full Backend Query Parameterization**: All filter criteria (`role`, `status`, `category`, `date ranges`, `search terms`) MUST be passed as query parameters down to the repository SQL query (`WHERE` clauses).
- **Synchronous Page Reset**: Frontend filter state updates MUST reset the active page number to `1` to avoid landing on empty out-of-range offsets.

### XIII. Structured Generic Payload & Absolute Type Safety (MUST)
Entities requiring category-specific or polymorphic business data (e.g., `PermissionRequest`, polymorphic audit logs) MUST use structured JSON payloads managed by strict Strategy and Value Object patterns:
- **Prohibition of Loose Dictionaries and Dynamic Attributes**: Declaring `payload: dict[str, Any]` in domain entities, repositories, or schemas is strictly forbidden. Using dynamic attribute access (`getattr(obj, "field")`, `hasattr(...)`) to bypass static typing is strictly banned.
- **Pydantic Discriminated Unions as Value Objects**: All payload variants MUST be modeled as strongly typed, immutable Value Objects inheriting from a base payload (`ConfigDict(frozen=True)`), unified via a Pydantic Discriminated Union (`Field(discriminator="category")`).
- **Explicit Safe Type Casting**: When extracting raw dictionary/JSON data from the database into Domain Entities, attributes MUST be explicitly cast and validated through dedicated parsing utilities (e.g., `parse_datetime`, `parse_int` in `app.utils.parsers`). Leaving unparsed raw objects or suppressing linter checks with `# type: ignore` is strictly prohibited.
- **Mandatory Dependencies in Constructors**: All use cases, strategies, and domain services MUST declare mandatory dependencies as non-nullable arguments in `__init__`. Providing default `None` fallback parameters (e.g., `repo: SomeRepository | None = None`) for mandatory collaborators is strictly forbidden.

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

**Version**: 1.8.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-10-31
