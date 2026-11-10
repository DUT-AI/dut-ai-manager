# Implementation Plan: Tách biệt Soft Delete và Hỗ trợ Khóa chính UUID cho Domain Model

**Branch**: `059-uuid-optional-soft-delete` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/059-uuid-optional-soft-delete/spec.md`

## Summary

Triển khai cơ chế khóa chính UUIDv7 (tuần tự theo thời gian, tối ưu index B-Tree) và tách biệt tính năng xóa mềm (`is_deleted`) thành các mixin độc lập cho các Domain Entity và ORM Model mới trong tương lai. Nâng cấp `BaseRepository` để tự động nhận biết model có xóa mềm hay không và phân tách rõ ràng hai phương thức `soft_delete()` và `hard_delete()`, đảm bảo tính tương thích ngược 100% cho các domain hiện hữu dùng khóa chính số nguyên và xóa mềm.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: SQLAlchemy 2.0, Pydantic v2, FastAPI, Dishka  
**Storage**: PostgreSQL (Kiểu dữ liệu native `UUID` với SQLAlchemy `as_uuid=True`)  
**Testing**: pytest (`pytest-asyncio`, `pytest-cov`)  
**Target Platform**: Linux server / macOS / Docker Container  
**Project Type**: Backend REST API & Modular Monolith Clean Architecture  
**Performance Goals**: Sinh khóa chính UUIDv7 trong micro-giây, chèn bản ghi tuần tự O(1) vào B-Tree index của PostgreSQL, không phát sinh mệnh đề `WHERE is_deleted = false` đối với các bảng không hỗ trợ xóa mềm.  
**Constraints**: Bảo đảm Zero Regressions đối với toàn bộ các entity, ORM model và repository hiện hữu (User, Meeting, Homework, Violation, PermissionRequest, BonusPoint, v.v.).  
**Scale/Scope**: Áp dụng cho toàn bộ tầng dùng chung `app.shared` (Domain & Infrastructure).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Clean Architecture & Practical DDD Boundaries)**: PASS. Module sinh mã `uuid_utils.py` và `BaseGenericEntity`, `BaseUuidEntity` nằm hoàn toàn ở tầng Domain (`app.shared.domain`), không phụ thuộc vào ORM hay framework. Các mixin SQLAlchemy và BaseRepository nằm ở tầng Infrastructure (`app.shared.infrastructure`).
- **Principle IX (Pure Composition Over Base Use Cases & Modularity)**: PASS. Phân rã triệt để thành các mixin chuyên biệt (`SQLAlchemyTimestampMixin`, `SQLAlchemySoftDeleteMixin`, `SQLAlchemyAuditMixin`, `SQLAlchemyUuidPrimaryKeyMixin`) cho phép các model mới linh hoạt kết hợp (Composition) thay vì ép buộc kế thừa một monolithic base model.
- **Principle X (Contextual Field Ownership & Zero Redundant Backward Compatibility)**: PASS. Mỗi trường dữ liệu (`is_deleted`, `created_by`, timestamps, `id`) thuộc về mixin sở hữu chính xác vòng đời của nó.
- **Principle XIV (No Fake Optionals & Fail-Fast Parameter Contracts)**: PASS. Gọi `soft_delete()` trên model không hỗ trợ xóa mềm sẽ ném ngoại lệ rõ ràng (`NotImplementedError`) ngay lập tức thay vì bỏ qua âm thầm.

## Project Structure

### Documentation (this feature)

```text
specs/059-uuid-optional-soft-delete/
├── spec.md              # Đặc tả nghiệp vụ & User Stories
├── plan.md              # Kế hoạch triển khai (tệp này)
├── research.md          # Nghiên cứu kỹ thuật: UUIDv7 & Composable Mixins
├── data-model.md        # Hợp đồng dữ liệu & Thiết kế chi tiết
├── quickstart.md        # Hướng dẫn kiểm thử & Xác thực
├── checklists/
│   └── requirements.md  # Danh mục kiểm định chất lượng đặc tả
└── tasks.md             # Danh sách tasks (sinh bởi /speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   └── shared/
│       ├── domain/
│       │   ├── uuid_utils.py            # [NEW] RFC 9562 UUIDv7 generator
│       │   └── base_entity.py           # [UPDATE] BaseGenericEntity, BaseUuidEntity, SoftDeleteEntityMixin
│       └── infrastructure/
│           ├── base_model.py            # [UPDATE] Composable Mixins (Timestamp, SoftDelete, Audit, UUID PK)
│           └── base_repository.py       # [UPDATE] Generic ID support, dynamic soft-delete check, hard_delete()
└── tests/
    └── unit/
        └── test_uuid_and_optional_soft_delete.py  # [NEW] Unit tests cho UUIDv7, mixins & BaseRepository
```

**Structure Decision**: Tính năng thuộc về tầng nền tảng dùng chung (`app.shared`), phân tách chính xác giữa Domain (Pure Python + Pydantic) và Infrastructure (SQLAlchemy 2.0).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Không có vi phạm | Thiết kế bám sát Clean Architecture và các nguyên lý Hiến pháp | Không áp dụng |
