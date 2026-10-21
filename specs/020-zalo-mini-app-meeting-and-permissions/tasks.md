# Tasks: Đồng Bộ Tính Năng Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

**Input**: Design documents from `specs/020-zalo-mini-app-meeting-and-permissions/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1], [US2], [US3])
- Include exact file paths in descriptions

---

## Phase 1: Setup & Routing Foundation

**Purpose**: Định nghĩa đường dẫn và cấu hình nền tảng cho trang Chi tiết Buổi họp và dịch vụ API.

- [X] T001 Khai báo route `MEETING_DETAIL: '/meetings/:id'` trong `zalo-mini-app/dut-manager/src/constants/paths.ts`
- [X] T002 Đăng ký route `<Route path="/meetings/:id" element={<ProtectedRoute><MeetingDetailPage /></ProtectedRoute>} />` trong `zalo-mini-app/dut-manager/src/app.tsx`
- [X] T003 [P] Cập nhật `meetingService` với các phương thức bổ sung (`updateParticipantStatus`, `getMeetingOverallEvaluation`, `submitMeetingOverallEvaluation`, `submitTraineeEvaluation`, `submitTrainerEvaluation`) trong `zalo-mini-app/dut-manager/src/services/api/meeting.service.ts`

---

## Phase 2: User Story 1 - Chi tiết Buổi họp & Điểm danh (Priority: P1) 🎯 MVP

**Goal**: Cho phép thành viên xem đầy đủ thông tin buổi họp (Hero header, thống kê sĩ số, danh sách người tham dự) và tự thực hiện điểm danh bằng ảnh chụp ngay trên Zalo Mini App.

**Independent Test**:
1. Vào `CalendarPage`, click vào một buổi họp -> Chuyển hướng thành công sang `/meetings/:id`.
2. Giao diện `MeetingDetailPage` hiển thị Hero card, hàng số liệu thống kê sĩ số và danh sách người tham gia.
3. Người dùng bấm nút "Điểm danh", chọn/chụp ảnh -> Gửi ảnh điểm danh thành công, trạng thái cập nhật thành `JOINED`.

### Implementation Tasks for US1

- [X] T004 [P] [US1] Xây dựng component `MeetingHeroCard` hiển thị tiêu đề, thời gian, phòng họp, link online, số lượng ghế tối đa và trạng thái buổi họp trong `zalo-mini-app/dut-manager/src/features/schedule/MeetingHeroCard.tsx`
- [X] T005 [P] [US1] Xây dựng component `MeetingStatsCard` hiển thị các thẻ đếm sĩ số (Tổng tham gia, Có mặt/Đã tham gia, Vắng có phép, Vắng không phép, Đi trễ) trong `zalo-mini-app/dut-manager/src/features/schedule/MeetingStatsCard.tsx`
- [X] T006 [US1] Xây dựng tab `MeetingParticipantsTab` hiển thị danh sách người tham gia (avatar, tên, role, tag trạng thái) và nút trigger Điểm danh (chụp/tải ảnh) trong `zalo-mini-app/dut-manager/src/features/schedule/MeetingParticipantsTab.tsx`
- [X] T007 [US1] Tạo trang `MeetingDetailPage.tsx` tích hợp ZaUI `Header` (có nút back), `MeetingHeroCard`, `MeetingStatsCard`, và `MeetingParticipantsTab` trong `zalo-mini-app/dut-manager/src/pages/MeetingDetailPage.tsx`
- [X] T008 [US1] Cập nhật `CalendarPage.tsx` và `MeetingCard.tsx`: khi nhấn vào card buổi họp, chuyển hướng sang `/meetings/${meeting.id}` thay vì mở modal cũ trong `zalo-mini-app/dut-manager/src/pages/CalendarPage.tsx` và `zalo-mini-app/dut-manager/src/features/schedule/MeetingCard.tsx`

**Checkpoint**: User Story 1 hoàn thành - Thành viên có thể xem chi tiết buổi họp và điểm danh mượt mà trên di động.

---

## Phase 3: User Story 2 - Host Quản lý Trạng thái & Đánh giá Buổi họp (Priority: P2)

**Goal**: Host/Admin có thể đổi trạng thái tham dự của từng người (thủ công) và thực hiện đánh giá (Trainee Evaluation / Overall Evaluation) ngay trên điện thoại.

**Independent Test**:
1. Host mở `/meetings/:id` của buổi họp có `enable_evaluation = true`.
2. Tại tab "Người tham gia", Host click đổi trạng thái của thành viên -> Lưu thành công.
3. Chuyển sang tab "Đánh giá Trainee", chọn học viên, nhập điểm các tiêu chí và nhận xét -> Lưu thành công.
4. Chuyển sang tab "Tổng kết đánh giá", xem tổng quan và nhập đánh giá chung.

### Implementation Tasks for US2

- [X] T009 [P] [US2] Xây dựng modal chỉnh sửa trạng thái người tham dự `EditParticipantStatusModal` cho Host trong `zalo-mini-app/dut-manager/src/features/schedule/EditParticipantStatusModal.tsx`
- [X] T010 [P] [US2] Xây dựng modal chấm điểm học viên `TraineeEvaluationModal` (tiêu chí điểm số, comment) trong `zalo-mini-app/dut-manager/src/features/schedule/TraineeEvaluationModal.tsx`
- [X] T011 [US2] Xây dựng component `MeetingEvaluationTab` gồm 2 sub-tabs ("Đánh giá Trainee" và "Tổng kết buổi họp") sử dụng `Tabs` ZaUI trong `zalo-mini-app/dut-manager/src/features/schedule/MeetingEvaluationTab.tsx`
- [X] T012 [US2] Tích hợp `MeetingEvaluationTab` và modal sửa trạng thái vào `MeetingDetailPage.tsx` (chỉ hiển thị tab đánh giá khi `meeting.enable_evaluation = true`) trong `zalo-mini-app/dut-manager/src/pages/MeetingDetailPage.tsx`

**Checkpoint**: User Story 2 hoàn thành - Host và Trainer có thể điều hành, điểm danh và đánh giá buổi học hoàn toàn trên Zalo.

---

## Phase 4: User Story 3 - Quản lý Đơn phép Đầy đủ & Lọc Đa năng (Priority: P3)

**Goal**: Đồng bộ giao diện Quản lý Đơn phép như Web: hiển thị danh sách toàn bộ đơn, bổ sung bộ lọc đa năng (theo danh mục, trạng thái, đơn của tôi), và hoàn thiện nghiệp vụ nộp đơn đổi ca (`CHANGE_MEETING`) kèm đếm ghế trống.

**Independent Test**:
1. Vào trang `/permissions`, kiểm tra danh sách hiển thị các đơn của hệ thống theo quyền.
2. Thử nghiệm thanh bộ lọc: Lọc theo loại `CHANGE_MEETING`, `ABSENCE`, `LATE`, `POSTPONE` và toggle "Chỉ đơn của tôi".
3. Nhấn "Tạo đơn mới", chọn loại "Đổi buổi sinh hoạt": kiểm tra hiển thị số ghế trống `max_seat - (đăng ký - vắng)` của buổi họp đích.
4. Gửi đơn đổi ca thành công -> Đơn xuất hiện trên danh sách với tag `CHANGE_MEETING` màu tím.

### Implementation Tasks for US3

- [X] T013 [P] [US3] Nâng cấp component `PermissionFilters` hỗ trợ chọn danh mục dạng tabs/chips ngang, toggle switch "Đơn của tôi / Tất cả đơn", và dropdown trạng thái trong `zalo-mini-app/dut-manager/src/features/permission_request/PermissionFilters.tsx`
- [X] T014 [US3] Cập nhật hook `usePermissionManagement` để quản lý state bộ lọc mở rộng (`filterMine`, `statusFilter`), fetch danh sách với đầy đủ tham số và tự động tính ghế trống trong `zalo-mini-app/dut-manager/src/features/permission_request/usePermissionManagement.ts`
- [X] T015 [US3] Nâng cấp `PermissionFormModal`: khi chọn loại `CHANGE_MEETING`, hiển thị danh sách ca đích kèm số ghế còn trống (`còn X chỗ`), ngăn chặn submit nếu số ghế trống <= 0 trong `zalo-mini-app/dut-manager/src/features/permission_request/PermissionFormModal.tsx`
- [X] T016 [US3] Cập nhật `PermissionsPage.tsx` để đồng bộ layout hiển thị bảng/card đơn phép kèm tag trạng thái chuẩn hoá như Web trong `zalo-mini-app/dut-manager/src/pages/PermissionsPage.tsx`

**Checkpoint**: User Story 3 hoàn thành - Nghiệp vụ và giao diện đơn phép đạt 100% độ tương thích với hệ thống Web.

---

## Phase 5: Polish, Cross-Cutting & Verification

**Purpose**: Đảm bảo hiệu năng, tính thẩm mỹ, xử lý loading/error states và kiểm thử đồng bộ.

- [X] T017 Kiểm tra responsive, dark/light theme tokens và khoảng cách an toàn (safe area / bottom padding) trên mobile trong `zalo-mini-app/dut-manager/src/pages/MeetingDetailPage.tsx` và `PermissionsPage.tsx`
- [X] T018 Xử lý trạng thái tải (`Loading / Skeleton`) và thông báo lỗi thân thiện (`useSnackbar`) khi mất kết nối mạng
- [X] T019 Chạy kiểm thử End-to-End theo kịch bản trong `specs/020-zalo-mini-app-meeting-and-permissions/quickstart.md` và kiểm tra build Vite (`npm run build`) trong `zalo-mini-app/dut-manager`

---

## Dependencies & Execution Order

- **Phase 1 (Setup & Routing)**: Bắt buộc hoàn thành trước.
- **Phase 2 (US1 - MVP)**: Phụ thuộc Phase 1. Cung cấp trang `MeetingDetailPage` và luồng xem chi tiết + điểm danh.
- **Phase 3 (US2 - Evaluation)**: Phụ thuộc Phase 2 (mở rộng trên `MeetingDetailPage`).
- **Phase 4 (US3 - Permissions)**: Có thể thực hiện song song với Phase 2/3 vì thuộc module `permission_request`.
- **Phase 5 (Polish)**: Hoàn tất sau khi tất cả user stories đã hoàn thành.

---

## Parallel Execution Opportunities

- T004 (`MeetingHeroCard`) và T005 (`MeetingStatsCard`) có thể làm song song.
- T009 (`EditParticipantStatusModal`) và T010 (`TraineeEvaluationModal`) có thể làm song song.
- Toàn bộ Phase 4 (Permissions) có thể phát triển độc lập với Phase 2 và 3 (Meeting Detail).
