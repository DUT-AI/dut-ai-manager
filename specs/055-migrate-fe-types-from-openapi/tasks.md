# Tasks: Di chuyển toàn diện kiểu dữ liệu Frontend sang TypeScript types tự động sinh từ OpenAPI (Feature 055)

**Feature Branch**: `055-migrate-fe-types-from-openapi`  
**Created**: 2026-11-08  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Task List

### Phase 1: Chuẩn hóa 4 Module cốt lõi có độ vênh cao (P1)

- [x] T001 [P1] Chuẩn hóa `src/components/PageWrapper.tsx` với type-only import và định nghĩa `Variants` an toàn cho framer-motion/motion.
- [x] T002 [P1] Chuyển `BonusPointType` enum trong `src/features/activity/types/activity.types.ts` sang Object `as const` tương thích `erasableSyntaxOnly`.
- [x] T003 [P1] Thay thế các Zod schema phản hồi trong `src/features/activity/types/activity.types.ts` bằng `Schema<"BonusPointResponse">` và `Schema<"PermissionRequestResponse">`.
- [x] T004 [P1] Cập nhật `src/features/academic-report/types/report.types.ts` sang `Schema<"DashboardOverviewResponse">`, `Schema<"ReportResponse">`, `Schema<"TitleReportItem">`.
- [x] T005 [P1] Tách biệt logic truy vấn `Team Members` trong `src/pages/HomePage.tsx` dùng `userService.getUsers(1, 10)` thay vì đọc trường `recent_users` ảo từ DashboardOverview.
- [x] T006 [P1] Chuẩn hóa kiểu dữ liệu `team_ids` (`number[] | undefined`) trong `src/features/duty/components/CreateDutyModal.tsx` để không bị gán nhầm `number[][]`.
- [x] T007 [P1] Bổ sung null-check cho `onOpenSubmitModal` trong `src/features/duty/components/WeeklyDutyCalendar.tsx` và import `DutyChecklistItem` trong `src/features/duty/hooks/useDutyManagement.ts`.
- [x] T008 [P1] Cập nhật `src/features/notification/hooks/useInAppNotifications.ts` truy cập chuẩn trường `res.pagination?.total` (thay thế `res.meta`).
- [x] T009 [P1] Ép kiểu an toàn `convertedVapidKey as BufferSource` trong `src/features/pwa/hooks/useWebPush.ts`.
- [x] T010 [P1] Sửa kiểu nhận mảng `PermissionRequestResponse[]` trong `src/features/trash/pages/TrashPermissionRequestPage.tsx`.
- [x] T011 [P1] Sửa callback tab key type trong `src/features/users/pages/ProfilePage.tsx`.

---

### Phase 2: Dọn dẹp Zod API Schemas ở các module còn lại (P2)

- [x] T012 [P2] Thay thế các Zod schemas trong `src/features/auth/types/auth.types.ts` bằng `Schema<"TokenResponse">`, `Schema<"LoginRequest">`.
- [x] T013 [P2] Thay thế các Zod schemas trong `src/features/meeting/types/meeting.types.ts` bằng `Schema<"MeetingResponse">`, `Schema<"ParticipantResponse">`.
- [x] T014 [P2] Thay thế các Zod schemas trong `src/features/rbac/types/rbac.types.ts` bằng `Schema<"RoleResponse">`, `Schema<"PermissionResponse">`.
- [x] T015 [P2] Thay thế các Zod schemas trong `src/features/teams/types/team.types.ts` bằng `Schema<"TeamResponse">`, `Schema<"TeamMember">`.
- [x] T016 [P2] Thay thế các Zod schemas trong `src/features/violations/types/violation.types.ts` bằng `Schema<"ViolationResponse">`.
- [x] T017 [P2] Thay thế các Zod schemas trong `src/features/billing/types/billing.types.ts` và `src/features/expense/types/expense.types.ts` bằng các schema OpenAPI tương ứng.

---

### Phase 3: Kiểm thử Toàn diện & Xác nhận Build (P3)

- [x] T018 [P3] Chạy `npm run generate:api` để xác nhận đồng bộ types mới nhất từ backend.
- [x] T019 [P3] Chạy `npx tsc -b` kiểm tra tính toàn vẹn kiểu tĩnh toàn bộ frontend (yêu cầu 0 lỗi).
- [x] T020 [P3] Chạy `npm run build` (`tsc -b && vite build`) để xác nhận đóng gói production thành công.
