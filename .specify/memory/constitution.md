<!--
Sync Impact Report:
- Version: initial template -> v1.0.0
- Ratification Date: 2026-09-25
- Principles established:
  1. I. Clean Architecture & DDD Boundaries (MUST)
  2. II. Dependency Injection with Dishka (MUST)
  3. III. Unified UTC+7 Timezone & DateTime Integrity (MUST)
  4. IV. Event-Driven Decoupling & Asynchronous Handlers (MUST)
  5. V. API Backward Compatibility & Unified Response Format (MUST)
  6. VI. Idempotency & Network Resilience (MUST)
- Sections added: Security & Compliance Standards, Testing & Verification Gates, Governance
-->

# DUT AI Manager Constitution

## Core Principles

### I. Clean Architecture & DDD Boundaries (MUST)
Every business domain in `dut-ai-manager` (Meeting, Homework, Violation, Report, User, PermissionRequest) MUST strictly follow Clean Architecture / Domain-Driven Design layering:
- **Domain Layer (`domain/`)**: Pure business logic, Entities, Value Objects, and Domain Events. Must have ZERO dependencies on frameworks, databases, or third-party web APIs.
- **Application Layer (`application/`)**: Use Cases orchestrating domain logic, repositories, and domain event publishing.
- **Infrastructure Layer (`infrastructure/`)**: Database models (SQLAlchemy), repositories, external service clients (MinIO, Discord, Zalo).
- **Presentation / API Layer (`controller.py`, `schemas.py`)**: FastAPI routers, Pydantic schemas, permission dependencies.

### II. Dependency Injection with Dishka (MUST)
All dependencies (Repositories, Use Cases, External Services) MUST be registered in Dishka providers (`providers.py`) and resolved using `@inject` with `FromDishka[...]` in FastAPI controllers or async job containers. Direct ad-hoc instantiation of services/repositories inside controllers or application logic is strictly forbidden.

### III. Unified UTC+7 Timezone & DateTime Integrity (MUST)
All business operations, attendance checks, deadline calculations, and cron jobs MUST operate on the **UTC+7 (Asia/Ho_Chi_Minh)** timezone. Code MUST use `app.utils.datetime.get_current_utc7_time()` or parse client ISO strings to naive UTC+7 before performing domain comparisons.

### IV. Event-Driven Decoupling & Asynchronous Handlers (MUST)
Side effects such as third-party notifications (Discord bot webhooks/messages, Zalo Mini App messages), audit logs, and real-time SSE broadcasts MUST be triggered asynchronously via `EventBus` (`DomainEvent` and `EventHandler`). Synchronous blocking calls to external notification APIs inside transaction paths are prohibited.

### V. API Backward Compatibility & Unified Response Format (MUST)
Existing REST API endpoints consumed by the Web Frontend (`frontend/`) and Zalo Mini App (`zalo-mini-app/`) MUST maintain backward compatibility. All responses MUST follow the standardized envelope `ApiResponse[T]` with appropriate HTTP status codes. Breaking schema changes require explicit versioning or migration plans.

### VI. Idempotency & Network Resilience (MUST)
Any endpoint that records transactional state over unreliable networks (such as bulk check-in, card tap, check-out) MUST support idempotency keys (`client_event_id` / `event_id`) to prevent duplicate processing on client retries.

## Security & Compliance Standards

1. **Zero Secret Leakage**: No hardcoding of passwords, JWT secrets, Discord Bot tokens, MinIO credentials, or Zalo App secrets. All configurations MUST read from environment variables managed via `app.core.config.Settings`.
2. **Role-Based Access Control (RBAC)**: All administrative, modification, and deletion endpoints MUST enforce permission checks via `hasPermission(...)` and `CurrentUser`.
3. **Data Protection & Sanitization**: All file uploads MUST be validated for MIME type and stored in object storage (MinIO) with securely generated paths.

## Development Workflow & Quality Gates

1. **Test Verification**: Any change to domain entities, use cases, or critical calculations (e.g. Attendance 23:59 check, Capacity Monitor, Violation trigger) MUST be covered by automated unit/integration tests (`pytest`).
2. **Zero Regression Guarantee**: Changes to existing use cases MUST NOT break previously established test suites.
3. **Migration Integrity**: Database schema modifications MUST include corresponding Alembic migrations with reliable upgrade and downgrade paths.

## Governance

1. **Constitution Authority**: This Constitution is the supreme design and architectural contract for `dut-ai-manager`. All specifications, implementation plans, and tasks generated via Spec Kit MUST comply with its principles.
2. **Amendments**: Amendments to these principles require explicit documentation, version bumping, and rationale justification.
3. **Versioning**: Semantic Versioning rules apply:
   - **MAJOR**: Breaking modifications to architectural boundaries or core principles.
   - **MINOR**: Addition of new principles or major workflow standards.
   - **PATCH**: Non-semantic clarifications and wording updates.

**Version**: 1.0.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-09-25
