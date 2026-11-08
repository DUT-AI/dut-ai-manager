<!--
Sync Impact Report:
- Version: v1.11.0 -> v1.12.0
- Ratification Date: 2026-09-25
- Last Amended: 2026-11-08
- Principles added / enhanced:
  - XVII. Strongly-Typed Storage & Zero Raw Dictionary Columns (MUST) (NEW) -> Mandate that all JSON / flexible metadata columns in SQLAlchemy ORM and Domain Entities be strongly typed using Pydantic BaseModels or Discriminated Unions via custom TypeDecorators (`SubmissionDetailsJSON`), strictly prohibiting `dict[str, Any]` in ORM Mapped types and domain entities to prevent raw unstructured data drift.
- Rationale: Codifying strict type-safety for complex JSON/metadata storage across ORM models and Domain entities, eliminating raw unstructured dictionaries and defensive fallback logic.
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

### X. Zero Redundant Backward Compatibility & Contextual Field Ownership (MUST)
Both backend and frontend codebases MUST NOT retain redundant backward-compatibility layers, duplicate function aliases, or misplaced data fields:
- **Prohibition of Internal Aliases**: Never create redundant re-exports or aliases (e.g., `export const useSyncHomework = useSyncHomeworkFromQuiz` or duplicate endpoints) merely to avoid updating callers.
- **Refactor Call Sites Directly**: When renaming, refactoring, or consolidating functions, hooks, DTOs, or services, all consuming callers MUST be updated directly to use the canonical identifier.
- **Contextual Field Ownership & Single Source of Truth**: Every domain attribute MUST reside strictly on the entity that owns its lifecycle and business rules. Duplicating or storing attributes on parent entities (e.g., storing a `deadline` on `homeworks` when deadlines vary per assignee and postponed request) is strictly forbidden. The parent entity represents only universal metadata; relational and participant-specific attributes belong exclusively in child/association entities (`homework_assignees`).
- **Immediate Removal of Legacy Columns**: When migrating database fields to consolidated or per-assignee structures, legacy sparse or misplaced columns and their foreign key constraints MUST be promptly backfilled and dropped via migrations. Never maintain dual-write or sparse legacy columns out of hesitation to refactor.
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
- **Integration with Strict Parameter Contracts**: Constructors and strategy methods MUST declare required dependencies as non-nullable types in compliance with Principle XIV.

### XIV. No Fake Optionals & Fail-Fast Parameter Contracts (MUST)
All dependencies, parameters, and attributes that are required for business logic or operational correctness MUST be declared as strict, non-nullable types without default `None`:
- **Strict Constructor & Function Contracts**: Constructors (`__init__`), event handlers, domain helpers, and repository methods MUST NOT accept `Type | None = None` for dependencies or parameters that the code expects to be present. If an object requires a repository, API client, or context data to operate, that collaborator MUST be a mandatory, non-null parameter.
- **Strict Prohibition of False Defensive Code**: Writing defensive null-checks such as `if not self.repo: return None` or `if self.repo is not None:` for mandatory collaborators is strictly prohibited. False defensive coding silently hides DI misconfigurations, broken call-sites, and test bugs at startup, turning compile-time or initialization failures into hard-to-trace runtime defects.
- **Fail-Fast Behavior**: If a mandatory argument is missing, the system MUST fail immediately with a `TypeError` at instantiation/call-site rather than degrading silently or returning incomplete state.
- **No Dummy Fallback Defaults**: Domain entities and methods MUST NOT fabricate fallback values (e.g., defaulting a missing deadline to `datetime.now(timezone.utc)`) to mask missing required inputs. If required data is missing, the operation MUST raise a domain exception.
- **Model & DTO Purity**: Base DTOs and Domain Entities MUST NOT declare optional attributes (`field: Type | None = None`) purely because one specific lifecycle stage (such as creation or update) requires it. Separate Write DTOs (`*Create`, `*Update`) from canonical Read DTOs and Entities to maintain exact field semantics.

### XV. Unified Client Networking & Fail-Fast Session Renewal (MUST)
All client-to-server communication and session renewal mechanisms MUST follow strict canonical networking and fail-fast authentication contracts:
- **Canonical Client Instance**: All HTTP network communication on client applications (`frontend/`) MUST flow through the canonical, configured HTTP client (`axiosInstance`). Ad-hoc instantiation of raw `fetch()`, isolated `axios` instances, or disparate manual headers (such as reading `localStorage.getItem('access_token')`) for API requests is strictly forbidden.
- **Single-Flight & Queued Silent Refresh**: Token renewal MUST be executed silently and asynchronously via single-flight locking (`isRefreshing`) and a FIFO Promise queue (`failedQueue`). Each queued request replayed upon token refresh MUST be marked with `_retry = true` to prevent infinite refresh loops and unhandled race conditions.
- **Fail-Fast HTTP Status Codes & Guest Protection**: Session expiration and missing credential errors MUST return standard HTTP `401 Unauthorized` (via `BadRequestException(status_code=401)` on the backend), strictly prohibiting HTTP 200 responses with `{ is_success: false }` for authentication failures. The client interceptor MUST differentiate between unauthenticated guests (e.g. missing token) and expired sessions, preventing false alarm "Phiên đăng nhập đã hết hạn" notifications for visitors.
- **Environment-Aware Cookie Security & Active Account Integrity**: Auth cookies (`access_token`, `refresh_token`) MUST enforce `HttpOnly`, `SameSite=Lax`, and dynamic `Secure` flags (`secure=settings.is_cookie_secure`) bound to `settings.ENVIRONMENT == "production"`. Token issuing and renewal use cases (`RefreshTokenUseCase`) MUST verify account active status (`user.is_active`), immediately revoking token renewal rights for locked or inactive users.

### XVI. Single Source of Truth API Contracts & Automated Type Synchronization (MUST)
Tất cả các giao tiếp dữ liệu giữa Backend và Client (Frontend / Mini App) MUST tuân thủ nghiêm ngặt nguyên tắc nguồn chân lý duy nhất và sinh kiểu tự động:
- **Backend Schema as Single Source of Truth**: Pydantic DTOs tại tầng Application của Backend là nguồn chân lý duy nhất cho toàn bộ cấu trúc dữ liệu gửi và nhận. Cấm tuyệt đối việc tự định nghĩa hoặc suy đoán dữ liệu ảo trên Client mà không xuất phát từ Schema Backend.
- **Zero Manual Type Duplication & Type Drift Prevention**: Nghiêm cấm việc viết tay thủ công các interface/type độc lập trên Frontend cho các payload phản hồi từ Backend. Tất cả các định nghĩa kiểu TypeScript cho API phải được sinh tự động từ OpenAPI Specification (`http://127.0.0.1:8001/api/v1/openapi.json`) thông qua bộ công cụ chuẩn hóa (`openapi-typescript` / `npm run generate:api`).
- **Strict Generic Envelope Extraction**: Client API Services và React Query hooks phải sử dụng các generic type helper chuẩn hóa (`Schema<T>`, `ApiData<...>`) để trích xuất payload bên trong envelope `ApiResponse[T]`, đảm bảo an toàn kiểu tĩnh (Type Safety) tuyệt đối tại thời điểm biên dịch và IntelliSense gợi ý mã nguồn tự động.

### XVII. Strongly-Typed Storage & Zero Raw Dictionary Columns (MUST)
Tất cả các cột dữ liệu phức tạp dạng JSON/Metadata lưu trữ trong Database (SQLAlchemy ORM) và Domain Entities MUST được định kiểu mạnh bằng Pydantic BaseModels hoặc Discriminated Unions:
- **Strict Prohibition of Raw Dictionaries in ORM & Entities**: Nghiêm cấm khai báo `dict[str, Any]` hoặc `dict | None` trong `Mapped[...]` của SQLAlchemy ORM Models và trong thuộc tính của Domain Entities.
- **Automated Pydantic TypeDecorator for JSON Columns**: Các cột lưu trữ JSON phức tạp (như `details`, `metadata`) MUST sử dụng SQLAlchemy `TypeDecorator` (ví dụ `SubmissionDetailsJSON`) kế thừa từ `JSON`. TypeDecorator này chịu trách nhiệm tự động gọi `.model_dump()` khi lưu vào DB (`process_bind_param`) và deserialize tự động dict thô thành các Pydantic Value Objects cụ thể (`CodingSubmissionDetails | GameSubmissionDetails`) khi đọc từ DB (`process_result_value`).
- **Elimination of Defensive Fallback Soup**: Toàn bộ luồng xử lý từ ORM qua Entity đến Application DTO và Frontend API contract đều được bảo đảm kiểu tĩnh 100%, loại bỏ hoàn toàn các đoạn mã phòng thủ fallback mù quáng (`details.get("xyz") || details.get("abc")`).

## Security & Compliance Standards

1. **Zero Secret Leakage**: No hardcoding of passwords, JWT secrets, Discord Bot tokens, MinIO credentials, or Zalo App secrets. All configurations MUST read from environment variables managed via `app.core.config.Settings`.
2. **Role-Based Access Control (RBAC)**: All administrative, modification, and deletion endpoints MUST enforce permission checks via `hasPermission(...)` and `CurrentUser`.
3. **Data Protection & Sanitization**: All file uploads MUST be validated for MIME type and stored in object storage (MinIO) with securely generated paths.
4. **Cookie & Session Hardening**: Auth cookies must be HttpOnly with dynamic secure flag based on environment, and all token renewal must validate active user status (`user.is_active`).

## Development Workflow & Quality Gates

1. **Test Verification**: Any change to domain entities, use cases, or critical calculations (e.g. Attendance 23:59 check, Capacity Monitor, Violation trigger) MUST be covered by automated unit/integration tests (`pytest`).
2. **Zero Regression Guarantee**: Changes to existing use cases MUST NOT break previously established test suites.
3. **Migration Integrity**: Database schema modifications MUST include corresponding Alembic migrations with reliable upgrade and downgrade paths. **Alembic Revision ID Limit**: Migration revision IDs MUST NOT exceed 32 characters in length (e.g., `039_move_hw_dl_to_assignees`) to comply with PostgreSQL's `alembic_version.version_num VARCHAR(32)` column width constraint. Exceeding this limit causes immediate migration failures in production and staging environments.
4. **Production Build Validation**: Frontend refactorings MUST be validated via `npm run build` to verify zero TypeScript errors and bundle compilation health.

## Governance

1. **Constitution Authority**: This Constitution is the supreme design and architectural contract for `dut-ai-manager`. All specifications, implementation plans, and tasks generated via Spec Kit MUST comply with its principles.
2. **Amendments**: Amendments to these principles require explicit documentation, version bumping, and rationale justification.
3. **Versioning**: Semantic Versioning rules apply:
   - **MAJOR**: Breaking modifications to architectural boundaries or core principles.
   - **MINOR**: Addition of new principles or major workflow standards.
   - **PATCH**: Non-semantic clarifications and wording updates.

**Version**: 1.12.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-11-08
