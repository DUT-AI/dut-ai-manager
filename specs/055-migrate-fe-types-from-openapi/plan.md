# Implementation Plan: Di chuyển toàn diện kiểu dữ liệu Frontend sang TypeScript types tự động sinh từ OpenAPI (Feature 055)

**Feature Branch**: `055-migrate-fe-types-from-openapi`  
**Created**: 2026-11-08  
**Status**: In Progress  
**Spec**: [spec.md](./spec.md)

---

## Technical Context & Architecture

### System Components Involved
1. **Source of Truth**: Backend FastAPI OpenAPI (`http://127.0.0.1:8001/api/v1/openapi.json`).
2. **Type Generator**: `openapi-typescript` v7.13.0 -> `frontend/src/types/api.generated.d.ts`.
3. **Type Helpers**: `frontend/src/types/api.ts` xuất `Schema<T>`, `ApiPaths`, `ApiResponseBody<T>`, `ApiEndpointResponse<P, M>`.
4. **Target Feature Modules**:
   - `activity`: `BonusPointResponse`, `PermissionRequestResponse`, `PermissionRequestCreate`, `BonusPointType` enum/const.
   - `academic-report`: `DashboardOverviewResponse`, `ReportResponse`, `TitleReportItem`, `ParticipationStats`.
   - `duty`: `DutyResponse`, `WeeklyDutyClassDto`, `CreateDutyFormValues`, `WeeklyDutyCalendar`.
   - `notification`: `Notification`, `NotificationFilterParams`, `useInAppNotifications` pagination.
   - `pwa`: `useWebPush` BufferSource type casting.
   - `users`: `UserResponse`, `UserCreate`, `UserUpdate`, `ProfilePage` tab keys.
   - `pages`: `HomePage` dashboard overview vs recent users query separation.
   - `trash`: `TrashPermissionRequestPage` permission restore list type.
   - `auth`, `billing`, `expense`, `meeting`, `rbac`, `teams`, `violations`: Dọn dẹp các `z.object` API models sang `Schema<"T">`.

---

## Constitution Check

| Điều khoản | Nội dung | Đánh giá | Rationale |
| :--- | :--- | :---: | :--- |
| **Điều V** | Chuẩn hóa Envelope `ApiResponse[T]` | PASS | Mọi API response đều bao gồm `{ is_success, status_code, data, message, pagination }`. |
| **Điều X** | Single Source of Truth & Zero Redundancy | PASS | Loại bỏ toàn bộ `z.object` DTOs trên Frontend, chỉ lấy type từ backend OpenAPI. |
| **Điều XV** | Canonical HTTP Client `axiosInstance` | PASS | Tất cả service calls dùng `axiosInstance`. |
| **Điều XVI** | Automated Type Sync & No Manual Duplicate | PASS | 100% type phản hồi API dùng `Schema<"T">` từ `api.generated.d.ts`. |

---

## Phase 0: Research & Resolution of Unknowns

- **Tệp nghiên cứu**: [research.md](./research.md)
- **Quyết định 1**: Định nghĩa Enum an toàn với TypeScript flag `erasableSyntaxOnly: true`. Thay vì dùng `enum BonusPointType { ... }`, chuyển sang dùng Object literal `as const` (`export const BonusPointType = { ... } as const; export type BonusPointType = typeof BonusPointType[keyof typeof BonusPointType];`).
- **Quyết định 2**: Tách biệt `recent_users` khỏi `DashboardOverviewResponse`. Backend `DashboardOverviewResponse` chuẩn chỉ chứa: `permission_requests`, `bonus_points`, `violations`, `unsubmitted_homeworks`, `meetings`. Danh sách thành viên trong nhóm trên `HomePage.tsx` được tải độc lập bằng `userService.getUsers(1, 10)` có kiểu trả về `UserResponse[]`.
- **Quyết định 3**: Chuẩn hóa kiểu phân trang của Envelope từ Backend: trường chứa tổng số bản ghi là `res.pagination?.total` (thay thế hoàn toàn `res.meta?.total` của legacy code).

---

## Phase 1: Data Model, Contracts & Quickstart

- **Data Model**: [data-model.md](./data-model.md)
- **Contracts**: [contracts/api_contracts.md](./contracts/api_contracts.md)
- **Quickstart Guide**: [quickstart.md](./quickstart.md)

---

## Phase 2: Implementation Phases

### Phase 2.1: Sửa các lỗi kiểu và thay thế Schema cho Nhóm Module ưu tiên cao (P1)
1. `frontend/src/components/PageWrapper.tsx`: Type-only import `import type { ReactNode }`, định nghĩa `Variants` type-safe.
2. `frontend/src/features/activity/types/activity.types.ts`:
   - Chuyển `BonusPointType` sang `as const` object.
   - Thay thế `bonusPointResponseSchema`, `permissionRequestResponseSchema` bằng `Schema<"BonusPointResponse">`, `Schema<"PermissionRequestResponse">`.
3. `frontend/src/features/academic-report/types/report.types.ts`:
   - Thay `dashboardOverviewResponseSchema` bằng `Schema<"DashboardOverviewResponse">`.
   - Cập nhật các type báo cáo còn lại sang `Schema<"...">`.
4. `frontend/src/pages/HomePage.tsx`:
   - Query riêng `userService.getUsers(1, 10)` để hiển thị danh sách `Team Members` chuẩn kiểu `UserResponse`.
5. `frontend/src/features/duty/`:
   - Cập nhật `duty.types.ts` dùng `Schema<"DutyResponse">` và `Schema<"WeeklyDutyClassDto">`.
   - Sửa `CreateDutyModal.tsx`: bóc tách kiểu `team_ids` rõ ràng (`number[] | undefined`).
   - Sửa `WeeklyDutyCalendar.tsx`: null check `onOpenSubmitModal`.
   - Sửa `useDutyManagement.ts`: import đầy đủ `DutyChecklistItem`.
6. `frontend/src/features/notification/hooks/useInAppNotifications.ts`:
   - Sửa `res.meta?.total` -> `res.pagination?.total`.
7. `frontend/src/features/pwa/hooks/useWebPush.ts`:
   - Cast `convertedVapidKey as BufferSource`.
8. `frontend/src/features/trash/pages/TrashPermissionRequestPage.tsx`:
   - Sửa kiểu nhận mảng `PermissionRequestResponse[]`.
9. `frontend/src/features/users/pages/ProfilePage.tsx`:
   - Callback an toàn `onChange={(key) => setActiveTab(key as any)}`.

### Phase 2.2: Thay thế Zod Schemas còn lại ở các module khác (P2)
1. `auth.types.ts`: Dùng `Schema<"LoginRequest">`, `Schema<"TokenResponse">`,...
2. `meeting.types.ts`: Dùng `Schema<"MeetingResponse">`, `Schema<"ParticipantResponse">`,...
3. `rbac.types.ts`: Dùng `Schema<"RoleResponse">`, `Schema<"PermissionResponse">`,...
4. `teams.types.ts`: Dùng `Schema<"TeamResponse">`, `Schema<"TeamMember">`,...
5. `violations.types.ts`: Dùng `Schema<"ViolationResponse">`,...
6. `billing.types.ts` & `expense.types.ts`: Dùng schemas tương ứng từ OpenAPI.

### Phase 2.3: Verification & Rigorous Build (P3)
1. Chạy `npm run generate:api` xác nhận đồng bộ mới nhất.
2. Chạy `npx tsc -b` kiểm tra kiểu tĩnh (bắt buộc 0 error).
3. Chạy `npm run build` (`tsc -b && vite build`) xác nhận đóng gói production thành công.
