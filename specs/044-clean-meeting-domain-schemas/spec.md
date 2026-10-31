# Feature Specification: Loại bỏ `Any` & `getattr`, Chuẩn hóa Type Safety cho Meeting Domain & Schemas

**Feature Branch**: `044-clean-meeting-domain-schemas`  
**Created**: 2026-11-01  
**Status**: Ready for Planning  
**Input**: Phân tích và làm sạch việc lạm dụng `Any` và `getattr()` trong `meeting_schemas.py`, `participant_schemas.py`, `evaluation_schemas.py`, và `meeting.py`.

---

## 🎯 Bối cảnh & Vấn đề Cốt lõi

### 1. Câu hỏi từ User:
> *"Hiện tại tôi thấy có 1 vấn đề dùng Any và getattr rất nhiều, có phải do thuộc tính `participants: list[MeetingParticipant] = Field(default_factory=list)` của Meeting không? /speckit-plan Tôi muốn clean lại chỗ này"*

### 2. Phân tích nguyên nhân thực sự:
- **Một phần là do cấu trúc phẳng `Meeting.participants`**: Trước đây, `Meeting` gom chung toàn bộ người tham gia vào một danh sách phẳng `participants`. Khi chuyển đổi DTO sang giao diện, tầng Schemas phải dùng `getattr` để bóc tách động các thuộc tính và quan hệ lồng nhau.
- **Nguyên nhân sâu xa & căn bản nhất**:
  1. **Thiếu Type Hint cụ thể trong các mapper `from_domain`**: Các hàm `from_domain(cls, p: Any)`, `from_domain(cls, e: Any)` nhận tham số kiểu `Any` thay vì Domain Entities cụ thể (`Meeting`, `MeetingParticipant`, `MeetingOverallEvaluation`, `MeetingEvaluation`).
  2. **Tư duy phòng thủ quá đà (False Defensive Programming)**: Do tham số là `Any` hoặc trước đó có lúc truyền ORM Model, lúc truyền Dict, lúc truyền Domain Entity, lập trình viên đã dùng `getattr(obj, "field", default)` ở khắp mọi nơi (kể cả những thuộc tính bắt buộc của Entity như `p.role`, `s.criteria_code`, `e.average_score`).
  3. **Vi phạm Hiến pháp Điều XIV (No Fake Optionals & Fail-Fast Parameter Contracts)**: Lạm dụng `getattr()` làm mất khả năng kiểm tra lỗi tĩnh của MyPy/Pyright/IDE, che giấu các bug tiềm ẩn (silent bugs) khi schema hoặc entity đổi tên trường.

---

## 👥 User Scenarios & Testing

### User Story 1 - Type-Safe Domain Entity Mapping (Priority: P1)
Là lập trình viên Backend, tôi muốn các hàm `from_domain` trong các schemas nhận đúng kiểu Domain Entity (`DomainMeeting`, `MeetingParticipant`, `MeetingOverallEvaluation`, `MeetingEvaluation`) và truy cập trực tiếp các thuộc tính bằng cú pháp chuẩn `obj.field`, để IDE và Type Checker bắt được lỗi ngay khi compile, đồng thời loại bỏ toàn bộ `getattr()` và `Any`.

**Why this priority**: Đảm bảo an toàn kiểu dữ liệu (Strict Type Contracts), ngăn chặn hoàn toàn lỗi run-time do typo thuộc tính hoặc mismatch schema.

**Independent Test**:
- Kiểm tra mã nguồn bằng MyPy/Ruff/Pyright: Không còn xuất hiện `getattr` và `Any` trong 4 files schemas/domain của Meeting.
- Toàn bộ unit tests và API tests của Meeting chạy thành công 100%.

**Acceptance Scenarios**:
1. **Given** một instance Domain Entity `Meeting` hợp lệ, **When** gọi `MeetingResponse.from_domain(m)` hoặc `MeetingDetailResponse.from_domain(m)`, **Then** dữ liệu được ánh xạ trực tiếp từ `m.trainers`, `m.trainees`, `m.title`, v.v. mà không sử dụng bất kỳ lời gọi `getattr()` nào.
2. **Given** một instance Domain Entity `MeetingParticipant`, **When** gọi `ParticipantResponse.from_domain(p)`, **Then** `p` được định kiểu rõ ràng là `MeetingParticipant`, dữ liệu được ánh xạ trực tiếp `p.id`, `p.user_id`, `p.role`, `p.user.name` an toàn.
3. **Given** một instance Domain Entity `MeetingOverallEvaluation` hoặc `MeetingEvaluation`, **When** gọi `from_domain(e)`, **Then** tham số `e` được định kiểu chính xác, `e.scores`, `e.trainer`, `e.average_score` được truy cập tường minh, không có `getattr()`.

---

### User Story 2 - Tối ưu hóa Aggregate Root `Meeting` (Priority: P2)
Là kiến trúc sư phần mềm, tôi muốn Aggregate Root `Meeting` đóng gói rõ ràng các thuộc tính người tham gia (`trainers` và `trainees`) với các method quản lý nhất quán, loại bỏ việc dùng `getattr` ngay trong chính methods của Domain Entity.

**Why this priority**: `Meeting` là Aggregate Root trung tâm của domain. Logic lọc `trainers` và `trainees` phải tự nhiên, nhanh, và type-safe.

**Independent Test**:
- Chạy toàn bộ test suite `backend/tests/unit/test_meeting_domain.py` và `backend/tests/unit/test_meeting_use_cases.py`.

**Acceptance Scenarios**:
1. **Given** `Meeting` entity có danh sách `participants: list[MeetingParticipant]`, **When** truy cập property `m.trainers` hoặc `m.trainees`, **Then** logic lọc sử dụng trực tiếp `p.role == ParticipantRole.TRAINER` và `not p.is_deleted` mà không dùng `getattr(p, "is_deleted", False)`.
2. **Given** `MeetingParticipant` kế thừa `BaseEntity`, **Then** thuộc tính `is_deleted` đã có sẵn và đảm bảo kiểu `bool`.

---

## 🚫 Non-Goals (Những gì KHÔNG làm)
- Không thay đổi bảng cơ sở dữ liệu (`meetings`, `meeting_participants`). Database schema giữ nguyên vẹn.
- Không thay đổi hợp đồng API response JSON trả về cho frontend (Frontend vẫn nhận `trainers`, `trainees` như đã thỏa thuận ở Phase trước).
- Không phá vỡ chức năng của các Use Cases hay Repositories hiện có.
