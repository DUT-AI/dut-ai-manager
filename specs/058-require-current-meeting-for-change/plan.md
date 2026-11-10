# Implementation Plan: Bắt buộc chọn ca hiện tại và kiểm tra có mặt khi đổi buổi meeting

**Branch**: `058-require-current-meeting-for-change` | **Date**: 2026-11-10 | **Spec**: [specs/058-require-current-meeting-for-change/spec.md](specs/058-require-current-meeting-for-change/spec.md)

**Input**: Feature specification from `specs/058-require-current-meeting-for-change/spec.md`

## Summary

Chấn chỉnh quy trình tạo đơn đổi buổi sinh hoạt (`CHANGE_MEETING`):
- **Backend**: Đổi `old_meeting_id` trong `ChangeMeetingPayload` thành trường bắt buộc (`int`). Trong `ChangeMeetingStrategy.validate(...)`, kiểm tra người tạo đơn (`created_by`) bắt buộc phải là người tham gia hợp lệ (`is_deleted = False`) của `old_meeting_id`. Nếu không, lập tức raise lỗi HTTP 400.
- **Frontend & Zalo Mini App**: Bắt buộc chọn ca hiện tại trên giao diện, xóa bỏ tùy chọn rỗng "đăng ký mới", hiển thị thông báo lỗi rõ ràng.

## Technical Context

**Language/Version**: Python 3.12 (Backend) / TypeScript 5.x (Frontend Web & Zalo Mini App)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic V2, Ant Design  
**Storage**: PostgreSQL (`permission_requests`, `meeting_participants`, `meetings`)  
**Testing**: `pytest tests/unit/test_change_meeting_permission_request.py tests/api/test_change_meeting_api.py`, `npx tsc -b`  
**Target Platform**: Linux Server / Web Browser / Zalo Mini App  
**Performance Goals**: Không làm tăng latency kiểm tra đơn (< 50ms)  
**Constraints**: Bảo đảm dữ liệu toàn vẹn, ngăn chặn tình trạng chiếm chỗ ảo  

## Constitution Check

| Nguyên tắc Hiến pháp | Trạng thái | Đánh giá tuân thủ |
|---|---|---|
| **I. Clean Architecture & Practical DDD Boundaries** | PASS | Validation logic nằm trọn trong Application Strategy (`ChangeMeetingStrategy`), Domain Payloads giữ vững cấu trúc Pydantic Discriminated Union. |
| **XIII. Structured Generic Payload & Absolute Type Safety** | PASS | `ChangeMeetingPayload` kế thừa `BasePermissionPayload` với kiểu `old_meeting_id: int` chặt chẽ, không dùng loose dict. |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | PASS | Loại bỏ `old_meeting_id: int | None = None` vì ca hiện tại là bắt buộc trong nghiệp vụ chuyển ca. |
| **XVI. Single Source of Truth API Contracts** | PASS | Sau khi sửa payload, tái tạo lại `openapi.json` và đồng bộ TypeScript types. |

## Project Structure

```text
specs/058-require-current-meeting-for-change/
├── spec.md
├── plan.md
├── research.md
└── data-model.md
```

### Affected Source Files

```text
backend/
├── app/permission_request/domain/payloads.py
├── app/permission_request/application/strategies/change_meeting_strategy.py
└── tests/
    ├── unit/test_change_meeting_permission_request.py
    └── api/test_change_meeting_api.py

frontend/
├── src/features/rbac/components/permissions/PermissionFormModal.tsx
└── openapi.json

zalo-mini-app/
└── dut-manager/src/features/permission_request/PermissionFormModal.tsx
```

## Detailed Execution Steps

### Step 1: Cập nhật Backend Domain Payload
- Trong `backend/app/permission_request/domain/payloads.py`:
  - Đổi `old_meeting_id: int | None = None` thành `old_meeting_id: int`.

### Step 2: Cập nhật Validation trong `ChangeMeetingStrategy`
- Trong `backend/app/permission_request/application/strategies/change_meeting_strategy.py`:
  - Kiểm tra `if not old_meeting_id: raise HTTPException(400, "Vui lòng chọn buổi sinh hoạt hiện tại")`.
  - Truy vấn `old_meeting = self.meeting_repo.get_by_id(old_meeting_id)`.
  - Nếu không có: `raise HTTPException(404, "Không tìm thấy buổi sinh hoạt hiện tại đã chọn")`.
  - Kiểm tra `is_in_old = any(p.user_id == user_id and not p.is_deleted for p in old_meeting.participants)`.
  - Nếu `not is_in_old`: `raise HTTPException(400, "Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn")`.

### Step 3: Cập nhật Unit Tests & API Tests
- Sửa các test case cũ trong `backend/tests/unit/test_change_meeting_permission_request.py`:
  - Cập nhật mock `get_by_id` cho `meeting_repo`.
  - Thay test "đăng ký mới không có old_meeting_id" bằng test xác nhận bị từ chối nếu không có `old_meeting_id`.
  - Thêm test `test_change_meeting_rejects_when_user_not_participant_in_old_meeting`.
- Chạy `pytest` đảm bảo toàn bộ tests pass 100%.

### Step 4: Cập nhật Web Frontend
- `frontend/src/features/rbac/components/permissions/PermissionFormModal.tsx`:
  - Đặt `rules: [{ required: true, message: 'Vui lòng chọn buổi sinh hoạt hiện tại!' }]` cho `old_meeting_id`.
  - Bỏ `allowClear` và bỏ placeholder/tooltip nhắc đăng ký mới.

### Step 5: Cập nhật Zalo Mini App
- `zalo-mini-app/dut-manager/src/features/permission_request/PermissionFormModal.tsx`:
  - Nhãn `Buổi sinh hoạt hiện tại (đổi đi) *`.
  - Xóa option "Chưa có buổi học nào (Đăng ký mới)".
  - Validate bắt buộc trước khi submit.

### Step 6: Đồng bộ OpenAPI & Typecheck
- Xuất lại `frontend/openapi.json`.
- Chạy `npm run generate:api` và `npx tsc -b`.
