# Feature Specification: Di chuyển toàn diện kiểu dữ liệu Frontend sang TypeScript types tự động sinh từ OpenAPI (Single Source of Truth)

**Feature Branch**: `055-migrate-fe-types-from-openapi`  
**Created**: 2026-11-08  
**Status**: Ready for Planning  
**Input**: Yêu cầu người dùng: "Cố gắng fix kiểu gì để đi lâu dài, đừng fix theo kiểu chắp vá cho hết lỗi, Hãy bắt đầu bằng việc thay thế các zod schema API bằng type mới từ generate api"

---

## Bối cảnh & Mục tiêu Cốt lõi (Why & Strategic Vision)

Trong các chu kỳ phát triển trước đây, Frontend (`frontend/src/features/`) duy trì hàng chục tệp `*.types.ts` viết tay bằng `zod` (`z.object({ ... })`) để suy diễn kiểu cho các DTO trả về hoặc gửi lên API:
1. **Lệch pha hợp đồng dữ liệu (Type Drift)**: Khi Backend Pydantic thay đổi trường (ví dụ `user_id` -> `created_by`, đổi cấu trúc `pagination`, kiểu trả về danh sách,...), Frontend không tự động nhận biết, dẫn đến lỗi runtime âm thầm hoặc ép kiểu `any` vô tội vạ.
2. **Chi phí bảo trì kép & lãng phí runtime bundle**: Hàng trăm Zod schema chỉ để `z.infer<...>` mà hầu như không dùng để parse runtime ở tầng client, làm phình bundle và gây xung đột kiểu dữ liệu.
3. **Mục tiêu dài hạn (Long-term & Non-patchy)**:
   - Thay thế toàn bộ các Zod schema DTO API viết tay bằng `Schema<"TênSchema">` trích xuất trực tiếp từ `frontend/src/types/api.generated.d.ts` (được sinh tự động từ OpenAPI của Backend).
   - Chuẩn hóa toàn bộ Envelope `ApiResponse<T>` khớp 100% với backend: `{ is_success, status_code, data, message, pagination }`.
   - Giữ lại Zod **CHỈ** cho các schema validation form thuần client (như form rules của React Hook Form / Ant Design nếu có) hoặc tách biệt hoàn toàn giữa UI State và API Contract DTOs.
   - Đảm bảo lệnh kiểm tra kiểu tĩnh `tsc -b` pass 100% với 0 lỗi trên toàn bộ dự án mà không cần tắt các cờ nghiêm ngặt hay dùng ép kiểu `any`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chuẩn hóa Type cho các Module Cốt lõi (Activity, Report, Duty, Users) (Priority: P1)

Là một kỹ sư phần mềm, tôi muốn toàn bộ các module đang có lỗi và cảnh báo type (`activity`, `academic-report`, `duty`, `users`, `HomePage`) sử dụng trực tiếp các DTO từ `Schema<"T">` của OpenAPI, để mọi trường dữ liệu (thuộc tính, quan hệ, pagination) đều đồng bộ tuyệt đối với Backend.

**Why this priority**: Đây là các module đang có độ vênh kiểu dữ liệu lớn nhất với backend hiện tại, gây ra 22 lỗi khi bật `tsc -b`.

**Independent Test**:
- Kiểm tra các file: `activity.types.ts`, `report.types.ts`, `duty.types.ts`, `user.types.ts`.
- Mọi type như `BonusPointResponse`, `PermissionRequestResponse`, `DashboardOverviewResponse`, `UserResponse`, `DutyResponse` đều là `Schema<"...">`.
- Chạy `npx tsc -b` trong `frontend/` - các module này không phát sinh lỗi mismatch kiểu.

**Acceptance Scenarios**:
1. **Given** schema `DashboardOverviewResponse` ở Backend chỉ có `{ permission_requests, bonus_points, violations, unsubmitted_homeworks, meetings }`, **When** trang `HomePage.tsx` cần danh sách thành viên gần đây, **Then** component gọi đúng API `userService.getUsers(1, 10)` có kiểu trả về là `UserResponse[]`, không tự suy đoán trường `recent_users` ảo trên DashboardOverview.
2. **Given** enum `BonusPointType`, **When** biên dịch TypeScript với `erasableSyntaxOnly`, **Then** kiểu dữ liệu được định nghĩa dạng `as const` object hoặc type alias trích xuất từ OpenAPI, tương thích chuẩn TypeScript hiện đại.
3. **Given** API `getMyNotifications`, **When** trả về dữ liệu phân trang, **Then** client truy cập đúng trường `res.pagination?.total` (chuẩn `ApiResponse`), không dùng trường cũ `res.meta`.

---

### User Story 2 - Loại bỏ Zod API Schemas Thừa thãi trên Toàn bộ các Feature còn lại (Priority: P2)

Là một lập trình viên duy trì dự án, tôi muốn dọn dẹp toàn bộ các `z.object` đại diện cho API Response/Request trong `auth`, `billing`, `expense`, `meeting`, `rbac`, `teams`, `violations`, chuyển sang dùng `Schema<"T">` từ `api.generated.d.ts`, để dự án không còn code trùng lặp và đạt chuẩn Single Source of Truth.

**Why this priority**: Tạo nền tảng đồng nhất toàn diện cho Frontend, không để lại nợ kỹ thuật (technical debt) hay sự phân mảnh giữa các module.

**Independent Test**:
- Quét toàn bộ thư mục `frontend/src/features/*/types/*.types.ts`: không còn khai báo Zod schema mô tả Response API.
- Các API Services (`auth.service.ts`, `meeting.service.ts`, `violation.service.ts`,...) trả về các kiểu tương ứng từ `Schema<"...">`.

**Acceptance Scenarios**:
1. **Given** các tệp types trong các feature, **When** kiểm tra import, **Then** chỉ import `Schema` từ `@/types/api`, không import `zod` cho các struct phản hồi API.
2. **Given** Backend sinh lại `api.generated.d.ts` khi có API mới, **When** chạy `npm run generate:api`, **Then** Frontend tự động có gợi ý autocomplete cho toàn bộ DTO mới mà không cần viết lại interface nào.

---

### User Story 3 - Kiểm thử Build & Typecheck Nghiêm ngặt (Priority: P3)

Là một kỹ sư DevOps/QA, tôi muốn quy trình `npm run build` thực thi `tsc -b && vite build` hoàn toàn xanh (0 error), đồng thời lệnh `npm run typecheck` xác nhận tính toàn vẹn kiểu tĩnh của 100% tệp nguồn trong `src/`.

**Why this priority**: Đảm bảo chất lượng sản phẩm bền vững dài lâu, chặn đứng mọi lỗi phát sinh trước khi đóng gói production.

**Acceptance Scenarios**:
1. **Given** toàn bộ frontend codebase, **When** chạy `npx tsc -b`, **Then** tiến trình kết thúc với mã thoát `0` và không có bất kỳ lỗi nào.
2. **Given** lệnh `npm run build`, **When** thực thi, **Then** vừa kiểm tra kiểu tĩnh thành công vừa đóng gói Vite bundle hoàn tất.

---

## Phạm vi & Ranh giới (Scope & Non-Goals)

- **In Scope**:
  - Toàn bộ các tệp types tại `frontend/src/features/*/types/*.types.ts`.
  - Toàn bộ các API Services tại `frontend/src/features/*/services/*.service.ts`.
  - Các hooks và components liên quan trực tiếp đến các type lỗi hiện tại (`HomePage.tsx`, `CreateDutyModal.tsx`, `WeeklyDutyCalendar.tsx`, `PageWrapper.tsx`, `ProfilePage.tsx`, `TrashPermissionRequestPage.tsx`).
- **Non-Goals**:
  - Không viết lại logic nghiệp vụ Backend (Backend đã có đầy đủ schema chuẩn OpenAPI).
  - Không thay đổi thư viện UI (vẫn giữ Ant Design & Tailwind CSS).
  - Không xóa các validation schema của form nhập liệu cục bộ nếu form đó thực sự dùng Zod resolver để validate client-side input.

---

## Yêu cầu Phi chức năng & Kiến trúc (Architectural Principles)

1. **Hiến chương Điều XVI (Single Source of Truth)**:
   - Backend Pydantic là nguồn chân lý duy nhất.
   - Frontend lấy type qua `api.generated.d.ts` và helper `Schema<"T">`.
2. **Kiến trúc bền vững (Long-term maintainability)**:
   - Nghiêm cấm ép kiểu `as any` hay dùng `// @ts-ignore` để chữa cháy tạm thời.
   - Xử lý triệt để optional/nullability (`t?.name`, default fallback `[]`).
   - Tương thích cờ TypeScript hiện đại (`erasableSyntaxOnly`, `verbatimModuleSyntax`).
