# Research & Technical Decisions: Cho phép người tạo buổi sinh hoạt đánh giá buổi học

**Feature**: `026-fix-creator-meeting-evaluation`  
**Date**: 2026-10-24  
**Status**: Completed  

---

## Nghiên cứu 1: Truy vết và lưu trữ định danh Người tạo cuộc họp (`created_by`)

### Vấn đề hiện tại
- Trong `backend/app/meeting/controller.py`, endpoint `POST /api/v1/meetings` (`create_meeting`) nhận `current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.CREATE)]`, nhưng không truyền `current_user.id` vào `CreateMeetingUseCase.execute()`.
- `CreateMeetingUseCase` khởi tạo thực thể `Meeting(...)` không gán `created_by`.
- Khi lưu vào database trong `MeetingRepository.save()`, `orm.created_by` không được gán tường minh từ `domain.created_by`. Mặc dù `SQLAlchemyTimestampMixin` có `default=get_current_user_id`, việc dựa vào biến ngữ cảnh toàn cục (contextvar) trong môi trường async không đảm bảo nếu có middleware can thiệp hoặc trong các ngữ cảnh chạy ngầm.
- DTO phản hồi `MeetingResponse` và `MeetingDetailResponse` trong `backend/app/meeting/schemas.py` hoàn toàn **thiếu trường `created_by`**. Do đó, Pydantic loại bỏ trường này khi trả về JSON, khiến Frontend nhận `meeting.created_by === undefined`.

### Quyết định kỹ thuật
- **Quyết định**: 
  1. Mở rộng `CreateMeetingUseCase.execute()` để tiếp nhận tham số `creator_id: int | None = None`.
  2. Tại controller `create_meeting`, truyền `current_user.id` vào use case.
  3. Gán tường minh `created_by=creator_id` vào domain entity `Meeting` và đảm bảo `MeetingRepository.save()` gán `orm.created_by = domain.created_by`.
  4. Bổ sung trường `created_by: int | None = None` vào `MeetingResponse` (kèm cập nhật `from_domain`).

### Phương án thay thế đã cân nhắc
- *Phương án A: Chỉ dựa vào `meeting.trainer.id` để nhận diện*: Bị từ chối vì khi tạo meeting chưa có tính năng chọn Trainer riêng biệt, `trainer` được fallback từ `creator`. Nếu `created_by` bị thiếu, cả `creator` lẫn `trainer` đều bị mất dữ liệu. Bổ sung cả `created_by` và `trainer` mang lại tính nhất quán cao nhất theo đúng hợp đồng DTO mà Frontend đã định nghĩa trong `frontend/src/features/meeting/types/meeting.types.ts`.

---

## Nghiên cứu 2: Phân quyền linh hoạt cho API Đánh giá buổi học (RBAC & Resource Ownership)

### Vấn đề hiện tại
- Hai API đánh giá cốt lõi:
  - `POST /api/v1/meetings/{id}/evaluations/overall` (Đánh giá tổng thể buổi học)
  - `POST /api/v1/meetings/{id}/evaluations/trainer` (Đánh giá từng học viên)
- Cả hai đang kiểm tra phân quyền bằng:
  `current_user: Annotated[CurrentUser, hasPermission(MeetingPermission.CREATE)]`.
- Ràng buộc này bắt buộc người đánh giá phải có quyền tạo meeting toàn cục. Một thành viên tạo cuộc họp (hoặc Trainer được phân công) nhưng chỉ có vai trò thông thường (Member/Trainer) sẽ bị trả về lỗi **403 Forbidden** khi nhấn gửi đánh giá.

### Quyết định kỹ thuật
- **Quyết định**: Xây dựng dependency FastAPI kiểm tra quyền theo nguyên tắc Resource Ownership: `check_meeting_evaluation_permission(meeting_id, current_user, uc)`.
  - Quyền gửi đánh giá được cấp phép khi thỏa mãn **ít nhất một** trong các điều kiện:
    1. Người dùng có vai trò quản trị hệ thống (`admin`, `superadmin`, `leader`, `manager`) hoặc sở hữu quyền `MeetingPermission.CREATE` / `MeetingPermission.UPDATE`.
    2. Người dùng chính là Người tạo cuộc họp (`meeting.created_by == current_user.id`).
    3. Người dùng chính là Trainer của cuộc họp (`meeting.trainer and meeting.trainer.id == current_user.id`).
  - Áp dụng dependency này cho cả hai endpoint `overall` và `trainer` evaluation, loại bỏ việc ép cứng `MeetingPermission.CREATE`.

### Phương án thay thế đã cân nhắc
- *Phương án A: Thêm quyền mới `MeetingPermission.EVALUATE` vào hệ thống*: Đòi hỏi migration thêm permission vào bảng roles/permissions của database và gán lại cho từng role. Tuy nhiên, đánh giá buổi học là quyền gắn liền với buổi học cụ thể (Contextual / Resource-based Access Control), một Trainer chỉ được đánh giá buổi học mà họ phụ trách, không được đánh giá buổi học của người khác. Do đó, Resource Ownership là giải pháp chuẩn và an toàn nhất.

---

## Nghiên cứu 3: Nhận diện vai trò Trainer trên Web Frontend & Zalo Mini App

### Vấn đề hiện tại
- Tại Web Frontend ([`MeetingHeroHeader.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/meeting/components/MeetingHeroHeader.tsx#L72-L75) và [`MeetingParticipantsTab.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/meeting/components/MeetingParticipantsTab.tsx#L50-L53)):
  ```typescript
  const isTrainer =
    (meeting.created_by ? currentUserId === meeting.created_by : false) ||
    (meeting.trainer?.id ? currentUserId === meeting.trainer.id : false) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())) ?? false);
  ```
- Do Backend không trả về `meeting.created_by`, `meeting.created_by` luôn là `undefined`.
- Nếu người tạo meeting không có vai trò `admin/leader/superadmin/manager`, `isTrainer` tính ra `false`.
- Hậu quả:
  - Ẩn nút "Bật Đánh giá 2 chiều"
  - Ẩn nút "Trainer đánh giá buổi học"
  - Ẩn toàn bộ nút "Đánh giá" học viên trong bảng thành viên.
- Tại Zalo Mini App ([`MeetingDetailPage.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/zalo-mini-app/dut-manager/src/pages/MeetingDetailPage.tsx#L91-L93)):
  ```typescript
  const isTrainer =
    user?.id !== undefined &&
    (meeting.trainer?.id === user.id || meeting.created_by === user.id);
  ```
  Zalo Mini App cũng phụ thuộc hoàn toàn vào `meeting.created_by` và `meeting.trainer.id`.

### Quyết định kỹ thuật
- **Quyết định**:
  1. Khi Backend cập nhật trả về `created_by`, các điều kiện kiểm tra trên sẽ hoạt động chính xác.
  2. Bổ sung chuẩn hóa ép kiểu an toàn trên Frontend: `Number(meeting.created_by) === Number(currentUserId) || Number(meeting.trainer?.id) === Number(currentUserId)` để tránh sự cố lệch kiểu chuỗi/số (`string` vs `number`).
  3. Đảm bảo giao diện phản ánh đúng tức thì trạng thái đã đánh giá sau khi submit thành công.

---

## Bảng tổng hợp quyết định kiến trúc

| Hạng mục | Hiện trạng | Giải pháp phê duyệt | Rationale |
| :--- | :--- | :--- | :--- |
| **`CreateMeetingUseCase`** | Không nhận `creator_id` | Tiếp nhận `creator_id` và gán vào Domain Entity | Đảm bảo tính toàn vẹn dữ liệu từ lúc tạo |
| **`MeetingRepository.save`** | Không set `orm.created_by` từ entity | Gán `orm.created_by = domain.created_by` | Đảm bảo lưu đúng vào PostgreSQL |
| **`MeetingResponse` DTO** | Thiếu `created_by` | Thêm `created_by: int \| None = None` | Cung cấp dữ liệu cho Client nhận diện quyền |
| **Endpoint Evaluation** | Bắt buộc `hasPermission(MeetingPermission.CREATE)` | Sử dụng dependency `check_meeting_evaluation_permission` | Cho phép Creator/Trainer đánh giá buổi học của mình |
| **Client UI Condition** | Phụ thuộc `created_by` bị undefined | Khôi phục `created_by` & ép kiểu Number an toàn | Hiển thị đầy đủ các nút đánh giá cho Creator |
