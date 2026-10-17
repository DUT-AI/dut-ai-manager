# Feature Specification: Chuẩn Hóa Kiểm Tra Bài Nộp Qua Database & Bổ Sung Nút Sync Thủ Công (My Homeworks)

**Feature Branch**: `013-fix-my-homeworks-coding-submitted`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User requirement: "Thống nhất toàn bộ các API get submission sẽ check bằng DB thôi, sau đó tạo ra 1 nút sync cho người dùng nếu thấy chưa tồn tại bản ghi hợp lệ, chỉ có nút sync mới gọi API, còn lại thì check DB hết."

---

## 1. Phân Tích Hiện Trạng & Vấn Đề

1. **Hiện trạng gọi HTTP runtime khi đọc dữ liệu**:
   - Trong `GetHomeworksUseCase.get_assigned_to_user` (`GET /api/v1/homeworks/me`), mỗi lần user truy cập hay refresh trang, backend đều kích hoạt hàng loạt HTTP request sang Quiz API (`completed-members`, `leaderboard`) với timeout 5s.
   - Nếu Quiz API nghẽn mạng hoặc timeout, use case nhận về danh sách rỗng `[]` và hiển thị user thành "Chưa nộp", gây hiện tượng **lúc true lúc false** cực kỳ chập chờn và làm chậm tốc độ tải trang.
2. **Định hướng kiến trúc mới (DB-First)**:
   - **Mọi API tra cứu danh sách/trạng thái bài nộp (`GET /me`, `GET /report/unsubmitted`, v.v.) CHỈ đọc từ cơ sở dữ liệu nội bộ (`homework_submissions`)**:
     - Tốc độ phản hồi tức thì (O(ms)), không phụ thuộc vào trạng thái mạng hay thời gian sống của Quiz API.
     - Dữ liệu ổn định tuyệt đối 100%, không bao giờ bị nhảy trạng thái giữa true và false.
   - **Tác vụ gọi Quiz API chỉ xảy ra khi**:
     - Webhook tự động từ Quiz API gửi sang khi người dùng nộp bài.
     - Hoặc người dùng/admin chủ động bấm **nút "Đồng bộ từ Quiz" (Sync)** trên giao diện khi họ vừa làm bài xong trên hệ thống Quiz và muốn cập nhật ngay vào DUT AI Manager.

---

## 2. Yêu Cầu Chức Năng (Functional Requirements)

### 2.1 Backend (Application & Presentation)
- **FR-001 (DB-Only Reading)**: `GetHomeworksUseCase.get_assigned_to_user` và `get_unsubmitted_by_user` PHẢI loại bỏ hoàn toàn việc gọi HTTP ra Quiz API (`QuizSubmissionHelper.get_coding_completed_user_ids` / `get_game_completed_user_ids`). Toàn bộ việc xác định `coding_submitted`, `game_submitted`, `is_submitted` PHẢI dựa 100% vào các bản ghi trong bảng `homework_submissions` (`self.homework_repo`).
- **FR-002 (User Self-Sync API)**: Cung cấp endpoint cho phép học viên tự kích hoạt đồng bộ bài nộp của chính mình cho 1 bài tập (`POST /api/v1/homeworks/{homework_id}/sync`) với quyền `HomeworkPermission.READ` của học viên thay vì chỉ giới hạn cho quyền Admin (`CREATE`).
- **FR-003 (Consistent Submission Criteria)**:
  - `coding_submitted = True` khi có bản ghi submission type `CODING` (hoặc `is_passed == True`) trong DB.
  - `game_submitted = True` khi có bản ghi submission type `GAME` với `is_passed == True` trong DB.

### 2.2 Frontend (UI/UX)
- **FR-004 (Nút Đồng Bộ / Sync trên HomeworkCard)**:
  - Trên mỗi thẻ bài tập (`HomeworkCard`) trong `/dashboard/my-homeworks`, nếu bài tập chưa hoàn thành (`!isSubmitted`), hiển thị một nút hành động **"Đồng bộ kết quả" (Sync)** với icon `SyncOutlined`.
  - Khi học viên bấm nút:
    1. Hiển thị loading spinner trên nút.
    2. Gọi API đồng bộ kết quả từ Quiz API về DB.
    3. Tự động refetch lại danh sách `useMyHomeworks` và hiển thị thông báo `message.success("Đã đồng bộ kết quả thành công!")`.

---

## 3. User Scenarios & Acceptance Criteria

### User Story 1 - Tải Trang Danh Sách Bài Tập Nhanh & Ổn Định (Priority: P1)
**Given** học viên truy cập `/dashboard/my-homeworks`,
**When** trang nạp danh sách bài tập,
**Then** hệ thống đọc 100% từ cơ sở dữ liệu nội bộ, thời gian tải trang < 200ms, trạng thái bài tập giữ nguyên ổn định, không bao giờ bị chuyển từ "Đã nộp" thành "Chưa nộp".

### User Story 2 - Học Viên Chủ Động Đồng Bộ Khi Vừa Làm Xong (Priority: P2)
**Given** học viên vừa nộp bài trên hệ thống Quiz nhưng webhook chưa kịp gửi về hoặc bài tập chưa hiển thị "Đã nộp",
**When** học viên bấm nút "Đồng bộ" trên thẻ bài tập tương ứng,
**Then** hệ thống gọi Quiz API lấy kết quả mới nhất lưu vào DB và cập nhật ngay trạng thái "Đã nộp" trên màn hình.

---

## 4. Success Criteria

- **SC-001**: 0 request HTTP gọi ra bên ngoài Quiz API trong luồng `GET /api/v1/homeworks/me`.
- **SC-002**: 100% giải quyết triệt để lỗi chập chờn lúc true lúc false.
- **SC-003**: Nút Sync hoạt động mượt mà, phản hồi rõ ràng kết quả cho học viên.
