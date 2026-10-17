# Feature Specification: Tách Biệt Use Cases Đơn Nhiệm Miền Điểm Thưởng (Bonus Point Modular Use Cases)

**Feature Branch**: `011-bonus-point-modular-use-cases`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Tôi muốn refactor file use case thành các file riêng lẽ như module meeting - xóa hoàn toàn use_cases.py, không cần tương thích ngược"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách Biệt Các Use Case CRUD Điểm Thưởng Thành Các File Đơn Nhiệm (Priority: P1)

Nhà phát triển và hệ thống bảo trì có thể dễ dàng định vị, kiểm thử và mở rộng từng use case thao tác điểm thưởng (Tra cứu, Tạo mới, Chỉnh sửa, Xóa, Phục hồi) trong một tệp nguồn riêng biệt thay vì tập trung trong một tệp nguyên khối `use_cases.py`, tuân thủ nghiêm ngặt Điều lệ Dự án (Constitution Principle VII).

**Why this priority**: Đây là yêu cầu cốt lõi nhằm giải quyết tình trạng vi phạm nguyên tắc Single Responsibility (SRP) ở tầng Application, chuẩn hóa cấu trúc thư mục tương tự như miền `meeting`.

**Independent Test**: Mỗi use case CRUD (`get_bonus_points_use_case.py`, `create_bonus_points_use_case.py`, `update_bonus_point_use_case.py`, `delete_bonus_point_use_case.py`, `restore_bonus_point_use_case.py`) có thể được import, khởi tạo và kiểm thử độc lập mà không cần nạp toàn bộ các use case còn lại.

**Acceptance Scenarios**:

1. **Given** một yêu cầu tra cứu danh sách điểm thưởng, **When** hệ thống thực thi, **Then** nghiệp vụ được đảm nhiệm bởi `GetBonusPointsUseCase` nằm độc lập trong tệp `get_bonus_points_use_case.py`.
2. **Given** một yêu cầu tạo mới điểm thưởng cho người dùng, **When** hệ thống thực thi, **Then** nghiệp vụ được đảm nhiệm bởi `CreateBonusPointsUseCase` trong `create_bonus_points_use_case.py` và phát ra sự kiện miền tương ứng.
3. **Given** một yêu cầu cập nhật, xóa hoặc phục hồi bản ghi điểm thưởng, **When** hệ thống xử lý, **Then** mỗi nghiệp vụ được đảm trách bởi chính xác một tệp use case tương ứng (`update_bonus_point_use_case.py`, `delete_bonus_point_use_case.py`, `restore_bonus_point_use_case.py`).

---

### User Story 2 - Tách Biệt Use Case Tính Điểm Hoạt Động CLB Chạy Tự Động (Priority: P2)

Use case tính điểm hoạt động CLB theo chu kỳ nền (`CalculateActivityPointsUseCase`) được tách thành một tệp độc lập chuyên trách, giúp các tiến trình chạy nền (Background Job) chỉ cần phụ thuộc vào chính xác nghiệp vụ này mà không bị gắn liền với các logic CRUD của API người dùng.

**Why this priority**: Tách biệt luồng tác vụ nền (Scheduled Jobs) khỏi luồng HTTP API thông thường, nâng cao tính độc lập và khả năng mở rộng.

**Independent Test**: Tiến trình nền `activity_scoring_job` có thể resolve và thực thi `CalculateActivityPointsUseCase` từ tệp riêng lẻ `calculate_activity_points_use_case.py` và kiểm thử thành công qua mock dữ liệu điểm danh.

**Acceptance Scenarios**:

1. **Given** tiến trình quét điểm hoạt động chạy theo lịch, **When** tiến trình yêu cầu dependency `CalculateActivityPointsUseCase`, **Then** hệ thống khởi tạo use case từ tệp chuyên biệt và tính toán điểm thưởng cho các thành viên hoàn thành buổi sinh hoạt.

---

### User Story 3 - Xóa Bỏ Hoàn Toàn Tệp Monolithic và Chuẩn Hóa Import Qua Gói Application (Priority: P3)

Gói ứng dụng `app.bonus_point.application` xuất khẩu (re-export) toàn bộ 6 use case thông qua `__init__.py` với danh sách `__all__` minh bạch theo đúng chuẩn Constitution Principle VII. Tệp nguyên khối cũ `use_cases.py` bị xóa bỏ hoàn toàn. Toàn bộ các import trong `providers.py`, `controller.py`, và `app/jobs/activity_scoring_job.py` được chuyển đổi sang import trực tiếp từ `app.bonus_point.application`.

**Why this priority**: Làm sạch triệt để mã nguồn, tránh nợ kỹ thuật (technical debt) từ các file shim dư thừa khi chỉ có 3 điểm gọi trong toàn bộ codebase.

**Independent Test**: Chạy `grep` toàn bộ codebase xác nhận không còn bất kỳ dòng nào tham chiếu tới `app.bonus_point.application.use_cases`, tệp `use_cases.py` không còn tồn tại trên ổ đĩa, và toàn bộ hệ thống khởi động, chạy test thành công 100%.

**Acceptance Scenarios**:

1. **Given** tệp `use_cases.py` bị xóa bỏ hoàn toàn, **When** khởi động ứng dụng hoặc chạy test, **Then** `providers.py`, `controller.py` và `activity_scoring_job.py` nạp use cases thành công từ `app.bonus_point.application` mà không gặp bất kỳ lỗi `ImportError` nào.

---

### Edge Cases

- **Tên use case số nhiều vs số ít**: `CreateBonusPointsUseCase` và `GetBonusPointsUseCase` (có 's' do thao tác nhiều user/records) giữ nguyên đúng tên class để không làm hỏng dependency injection của Dishka.
- **Tuần hoàn phụ thuộc (Circular Dependency)**: Đảm bảo giữa các use case mới không import chéo nhau mà chỉ phụ thuộc vào Repository, EventBus, DTOs và Domain Entities.
- **Sự kiện miền (Domain Events)**: Việc xuất bản các sự kiện miền `BonusPointCreated`, `BonusPointUpdated`, `BonusPointDeleted` trong các use case riêng lẻ phải giữ nguyên vẹn 100% payload và thời điểm phát sóng.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI chia tách 6 use case trong `backend/app/bonus_point/application/use_cases.py` thành 6 tệp nguồn riêng biệt theo quy ước `*_use_case.py`:
  - `get_bonus_points_use_case.py`
  - `create_bonus_points_use_case.py`
  - `update_bonus_point_use_case.py`
  - `delete_bonus_point_use_case.py`
  - `restore_bonus_point_use_case.py`
  - `calculate_activity_points_use_case.py`
- **FR-002**: Tệp `backend/app/bonus_point/application/__init__.py` PHẢI re-export toàn bộ 6 use case này và định nghĩa danh sách `__all__` đầy đủ theo Điều lệ Dự án (Constitution Principle VII).
- **FR-003**: Hệ thống PHẢI xóa bỏ hoàn toàn tệp `backend/app/bonus_point/application/use_cases.py`, không duy trì file shim.
- **FR-004**: Tệp Dishka Provider (`backend/app/bonus_point/providers.py`), Controller (`backend/app/bonus_point/controller.py`), và tác vụ nền (`backend/app/jobs/activity_scoring_job.py`) PHẢI được cập nhật import trực tiếp từ `app.bonus_point.application`.
- **FR-005**: Toàn bộ logic nghiệp vụ, tính toán điểm số và sự kiện thông báo (`EventBus.publish`) PHẢI được bảo toàn nguyên vẹn 100%.

### Key Entities *(include if feature involves data)*

- **BonusPoint (Thực thể Điểm Thưởng)**: Đại diện cho bản ghi điểm thưởng/cộng trừ điểm của thành viên.
- **BonusPointType (Phân loại Điểm Thưởng)**: Giá trị phân loại lý do cộng điểm (hoạt động CLB, đóng góp, khác).
- **Domain Events**: `BonusPointCreated`, `BonusPointUpdated`, `BonusPointDeleted`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các use case trong miền điểm thưởng được đặt trong các tệp riêng biệt theo quy ước `*_use_case.py`.
- **SC-002**: Tệp `use_cases.py` được loại bỏ hoàn toàn (0 file nguyên khối trong thư mục application).
- **SC-003**: 0 lỗi `ImportError` trên toàn bộ hệ thống backend khi chuyển đổi cấu trúc file.
- **SC-004**: Đạt tỷ lệ vượt qua 100% (Zero Regression) trên toàn bộ các bài kiểm thử liên quan đến điểm thưởng (`test_bonus_point_api.py`, `test_billing_use_cases.py`, v.v.).

## Assumptions

- Các DTO (`BonusPointCreate`, `BonusPointUpdate`) và Repository (`BonusPointRepository`, `ParticipantRepository`) giữ nguyên vị trí và interface.
- Việc đăng ký DI trong Dishka container tiếp tục hoạt động thông qua việc resolve các lớp use case theo tên class đã định.
