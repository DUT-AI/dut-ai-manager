# Feature Specification: Chuẩn hóa Kiến trúc Thời gian Toàn diện (Enterprise UTC Datetime)

**Feature Branch**: `028-enterprise-utc-datetime-refactor`  
**Created**: 2026-10-30  
**Status**: Draft  
**Input**: Chuẩn hóa toàn bộ việc xử lý thời gian theo Cách 4 (Lưu UTC, Ingestion Auto-detect/Convert, Hiển thị UTC+7), loại bỏ hoàn toàn anti-pattern `get_current_utc7_time()`.

---

## 1. Tóm tắt & Bối cảnh Nghiệp vụ

Hiện tại hệ thống `dut-ai-manager` đang sử dụng hàm `get_current_utc7_time()` rải rác khắp hàng chục file Use Case, Model, Repository và Background Scanner. Hàm này lấy giờ UTC hiện tại cộng thêm 7 tiếng rồi cắt bỏ thông tin múi giờ (`replace(tzinfo=None)`) để lưu con số giờ địa phương vào các cột `TIMESTAMP WITHOUT TIME ZONE`.

### Vấn đề:
1. **Rủi ro người dùng/lập trình viên quên gọi hàm**: Bất kỳ khi nào một lập trình viên sử dụng `datetime.now()` mặc định của Python trên môi trường server/Docker (chạy UTC), dữ liệu thời gian sẽ bị lệch 7 tiếng so với thực tế, gây sai lệch nghiêm trọng về deadline bài tập, giờ họp, cảnh báo vi phạm và lịch nhắc nhở.
2. **Vi phạm chuẩn kiến trúc doanh nghiệp**: Không đồng nhất giữa aware datetime và naive datetime, cản trở việc mở rộng, tích hợp bên thứ ba và tiềm ẩn lỗi so sánh `can't compare offset-naive and offset-aware datetimes`.
3. **Phụ thuộc quá nhiều vào hàm tiện ích thủ công**: Thay vì hệ thống tự động hóa ở tầng ORM và tầng DTO Ingestion, lập trình viên phải nhớ import và gán thủ công `created_at`, `updated_at`.

### Giải pháp (Cách 4 - Enterprise UTC Architecture):
- **Tầng Database**: Chuyển đổi toàn bộ cột thời gian sang `TIMESTAMPTZ` (SQLAlchemy `DateTime(timezone=True)`). Mọi bản ghi lưu trữ theo chuẩn UTC tuyệt đối.
- **Tầng Ingestion (DTO / API Gate)**: Sử dụng Pydantic custom validator `UtcDateTime`. Tự động nhận diện chuỗi ISO từ Client; nếu chuỗi thiếu múi giờ (như format hiện tại của Frontend `YYYY-MM-DDTHH:mm:ss`), tự động quy ước là giờ Việt Nam (`Asia/Ho_Chi_Minh`) và chuyển về UTC aware.
- **Tầng Domain / Application (Use Cases)**: Sử dụng chuẩn mực Python 3.11+ `datetime.now(timezone.utc)`. Loại bỏ 100% việc gọi `get_current_utc7_time()`.
- **Tầng Presentation (Output)**: API trả về chuẩn ISO 8601 UTC (kèm `Z` hoặc offset `+07:00`). Frontend (`dayjs`) tự động định dạng giờ theo múi giờ thiết bị/Việt Nam.

---

## 2. User Scenarios & Testing (Bắt buộc)

### User Story 1 - Tự động chuẩn hóa thời gian đầu vào từ Client mà không cần đổi Frontend (Priority: P1)
**Mô tả**: Người dùng tạo mới hoặc cập nhật Meeting/Homework/Duty trên giao diện Web hoặc Zalo Mini App. Client gửi chuỗi thời gian dạng `2026-10-31T19:30:00` (không kèm offset). Backend tự động hiểu đây là 19:30 giờ Việt Nam và chuyển thành `2026-10-31T12:30:00Z` lưu vào DB mà không bị lệch 7 tiếng.

**Acceptance Scenarios**:
1. **Given** Client gửi payload meeting có `start_time = "2026-10-31T19:30:00"`, **When** DTO parse dữ liệu, **Then** trường `start_time` trong Python là `datetime(2026, 10, 31, 12, 30, tzinfo=timezone.utc)`.
2. **Given** Client gửi payload có offset `start_time = "2026-10-31T19:30:00+07:00"`, **When** DTO parse dữ liệu, **Then** giá trị lưu vào DB vẫn là `2026-10-31T12:30:00Z`.
3. **Given** Client gửi payload UTC chuẩn `start_time = "2026-10-31T12:30:00Z"`, **When** DTO parse dữ liệu, **Then** giá trị nhận được vẫn là `2026-10-31T12:30:00Z`.

---

### User Story 2 - So sánh thời gian chính xác tuyệt đối trong mọi Use Case (Priority: P1)
**Mô tả**: Khi hệ thống kiểm tra hạn nộp bài tập (`deadline < now`), kiểm tra điểm danh buổi họp hoặc chạy background scanner quét nhắc nhở (`scan_and_send_reminders`), hệ thống so sánh trực tiếp `datetime.now(timezone.utc)` với các trường thời gian trong entity (đều là UTC aware).

**Acceptance Scenarios**:
1. **Given** Một bài tập có hạn nộp lúc 19:30 giờ VN (`12:30Z`), **When** Đồng hồ thực tế là 19:31 giờ VN (`12:31Z`), **Then** Điều kiện `deadline < datetime.now(timezone.utc)` trả về `True` (quá hạn) chính xác đến từng giây.
2. **Given** Scanner quét nhắc nhở cuộc họp sắp diễn ra trước 30 phút, **When** Thời gian hiện tại đạt mốc `start_time - 30 minutes`, **Then** Scanner nhận diện chính xác task cần gửi thông báo mà không phụ thuộc vào timezone của máy chủ hay Docker host.

---

### User Story 3 - Tự động hóa Audit Timestamps ở tầng ORM Model (Priority: P2)
**Mô tả**: Lập trình viên tạo entity mới hoặc cập nhật bản ghi không cần phải gán thủ công `created_at` hay `updated_at`. `SQLAlchemyTimestampMixin` tự động gán `datetime.now(timezone.utc)` ở tầng application và `server_default=func.now()` ở tầng database.

**Acceptance Scenarios**:
1. **Given** Một model kế thừa `SQLAlchemyTimestampMixin`, **When** Insert bản ghi mới không truyền `created_at`, **Then** Bản ghi được lưu với `created_at` là timestamp UTC hiện tại.
2. **Given** Một bản ghi được update, **When** Thực thi commit, **Then** Cột `updated_at` tự động cập nhật thời điểm UTC mới nhất.

---

### User Story 4 - Di chuyển an toàn dữ liệu lịch sử trong Cơ sở Dữ liệu (Priority: P1)
**Mô tả**: Dữ liệu lịch sử hiện có trong database PROD (các cuộc họp cũ, bài tập cũ, điểm cộng cũ đang lưu naive giờ Việt Nam) phải được chuyển đổi chuẩn hóa sang `TIMESTAMPTZ` mà không làm thay đổi mốc giờ thực tế của người dùng.

**Acceptance Scenarios**:
1. **Given** Một bản ghi meeting cũ có `start_time = '2026-10-20 19:30:00'`, **When** Chạy Alembic migration, **Then** Cột đổi thành `TIMESTAMPTZ` và giá trị chuyển đổi thành `'2026-10-20 12:30:00+00'`.
2. **Given** Người dùng xem lại lịch sử trên Web/Zalo Mini App, **Then** Giao diện vẫn hiển thị đúng ngày 20/10/2026 lúc 19:30.

---

## 3. Phạm vi & Giới hạn (Scope & Boundaries)

- **In-Scope**:
  - Toàn bộ backend models, schemas, use cases, background tasks đang dùng `get_current_utc7_time`.
  - Migration script Alembic chuyển đổi schema database từ naive timestamp sang `TIMESTAMPTZ`.
  - Migration script dữ liệu cũ: quy ước dữ liệu naive hiện tại là `Asia/Ho_Chi_Minh` và chuyển đổi sang UTC.
  - Cập nhật Constitution Principle III sang mô hình UTC Enterprise.
  - Bật rule Linter `DTZ` trong `pyproject.toml` để bảo vệ mã nguồn vĩnh viễn.
- **Out-of-Scope**:
  - Không thay đổi logic nghiệp vụ của bất kỳ tính năng nào (Meeting, Homework, Violation, Duty, Reminder...).
  - Không yêu cầu sửa đổi đồng loạt toàn bộ mã nguồn Frontend vì tầng Ingestion DTO tự động tương thích ngược với định dạng chuỗi cũ.

---

## 4. Success Criteria

1. **Zero Call Sites**: Không còn bất kỳ file nào trong `backend/app/` phụ thuộc vào `get_current_utc7_time()`.
2. **100% Aware Datetime**: Tất cả so sánh thời gian trong domain và application layer đều sử dụng aware datetime UTC.
3. **Zero Test Regressions**: Toàn bộ test suite hiện có của backend (`pytest`) chạy pass 100%.
4. **Linter Gate Protection**: Ruff linter bật `DTZ` và pass 100%, tự động bắt lỗi nếu dev viết `datetime.now()` không khai báo timezone.
