# Tasks: Đồng bộ hóa hợp đồng API và sinh Type tự động cho Frontend từ OpenAPI Backend

**Input**: Design documents from `/specs/054-openapi-type-generation/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)  
**Feature Branch**: `054-openapi-type-generation`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Có thể chạy song song (khác file, không phụ thuộc nhau)
- **[Story]**: Thuộc User Story nào (`[US1]`, `[US2]`, `[US3]`)
- Bao gồm đường dẫn tệp chính xác trong mô tả công việc

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo và cấu hình thư viện cùng công cụ tự động hóa

- [x] T001 Cài đặt devDependency `openapi-typescript` vào `frontend/package.json`
- [x] T002 [P] Cấu hình script `"generate:api": "openapi-typescript http://127.0.0.1:8001/api/v1/openapi.json -o src/types/api.generated.d.ts"` trong `frontend/package.json`
- [x] T003 [P] Thêm target `frontend-generate-api` vào root `Makefile` để tự động kích hoạt sinh type

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Kiểm tra kết nối Backend và sinh tệp định nghĩa kiểu OpenAPI ban đầu

**⚠️ CRITICAL**: Phải hoàn thành giai đoạn này trước khi triển khai các User Story

- [x] T004 Kiểm tra và xác nhận backend FastAPI đang chạy và endpoint `http://127.0.0.1:8001/api/v1/openapi.json` trả về schema OpenAPI 3.1 hợp lệ
- [x] T005 Thực thi lệnh sinh type ban đầu để tạo tệp `frontend/src/types/api.generated.d.ts` từ OpenAPI schema backend

**Checkpoint**: Nền tảng tệp `api.generated.d.ts` sẵn sàng cho việc định nghĩa helpers và tích hợp vào các module.

---

## Phase 3: User Story 1 - Sinh mã Type tự động từ hợp đồng Backend qua Live URL (Priority: P1) 🎯 MVP

**Goal**: Đảm bảo quy trình sinh mã TypeScript từ Live URL `http://127.0.0.1:8001/api/v1/openapi.json` diễn ra trơn tru, đáng tin cậy, tái tạo được và có thông báo lỗi dễ hiểu khi backend chưa chạy.

**Independent Test**: Khởi động backend (`make backend-dev`), chạy `npm run generate:api` tại `frontend/` (hoặc `make frontend-generate-api`), kiểm tra tệp `frontend/src/types/api.generated.d.ts` được cập nhật chính xác với đầy đủ `components["schemas"]` và `paths`.

### Implementation for User Story 1

- [x] T006 [US1] Xác thực tính toàn vẹn của tệp `frontend/src/types/api.generated.d.ts`, đảm bảo chứa đầy đủ các Pydantic schema của hệ thống (như `HomeworkResponse`, `HomeworkResponseDetail`, `MeetingResponse`) và các `paths` API
- [x] T007 [US1] Cấu hình xử lý lỗi thân thiện trong lệnh sinh type hoặc script wrapper tại `frontend/package.json` để nhắc nhở lập trình viên chạy `make backend-dev` khi gặp lỗi `ECONNREFUSED`

**Checkpoint**: User Story 1 hoàn thành độc lập. Lập trình viên có thể sinh tệp kiểu dữ liệu từ backend bất cứ lúc nào bằng một câu lệnh.

---

## Phase 4: User Story 2 - Sử dụng Type Helper chuẩn hóa và tương thích Envelope ApiResponse (Priority: P2)

**Goal**: Cung cấp các type helper tập trung (`Schema<T>`, `ApiPaths`, `ApiResponseBody<T>`) giúp lập trình viên frontend truy cập kiểu dữ liệu nhanh chóng, có gợi ý IntelliSense đầy đủ và tương thích hoàn hảo với phong bì `ApiResponse[T]` (Hiến chương Điều V).

**Independent Test**: Khai báo biến thử nghiệm với `Schema<"HomeworkResponse">` và `ApiResponseBody<"HomeworkResponseDetail">` trong `frontend/src/types/api.ts` hoặc tệp test, xác nhận IDE gợi ý chính xác danh sách schema và TypeScript kiểm tra chặt chẽ các trường dữ liệu.

### Implementation for User Story 2

- [x] T008 [P] [US2] Xây dựng module type helper tại `frontend/src/types/api.ts` xuất khẩu `Schema<T extends keyof components["schemas"]>`, `ApiPaths`, `ApiResponseBody<T>`, và `ApiEndpointResponse<P, M>` theo đúng hợp đồng trong `specs/054-openapi-type-generation/contracts/type_helper_contract.md`
- [x] T009 [US2] Re-export các utilities từ `frontend/src/types/api.ts` vào `frontend/src/types/index.ts` để các module trong toàn bộ frontend có thể import trực tiếp từ `@/types`

**Checkpoint**: User Story 1 và User Story 2 hoạt động hoàn chỉnh. Toàn bộ frontend có thể sử dụng `Schema<T>` và `ApiPaths` một cách thống nhất.

---

## Phase 5: User Story 3 - Áp dụng thử nghiệm mẫu (Pilot) an toàn cho Module Homework (Priority: P3)

**Goal**: Chuyển đổi các định nghĩa kiểu viết tay trong module `Homework` sang sử dụng các schema sinh tự động từ `Schema<T>`, chứng minh tính khả thi của Single Source of Truth và cam kết zero-regression.

**Independent Test**: Toàn bộ module `frontend/src/features/homework/` (services, components, hooks) biên dịch thành công với các types mới từ `Schema<T>`, không có lỗi kiểu TypeScript khi chạy `npm run build` và `npm run lint`.

### Implementation for User Story 3

- [x] T010 [US3] Tái cấu trúc các interface DTO trong `frontend/src/features/homework/types/homework.types.ts`: thay thế các khai báo viết tay bằng `Schema<"HomeworkResponse">`, `Schema<"HomeworkResponseDetail">`, `Schema<"HomeworkCreate">`, `Schema<"HomeworkUpdate">`, `Schema<"ExerciseSummary">`, `Schema<"HomeworkReportResponse">`, và `Schema<"HomeworkSubmissionStatusResponse">`
- [x] T011 [US3] Cập nhật các phương thức gọi API trong `frontend/src/features/homework/services/homework.service.ts` để sử dụng trực tiếp các kiểu dữ liệu chuẩn hóa từ `homework.types.ts`
- [x] T012 [US3] Rà soát và đảm bảo tính tương thích của các components và utils trong `frontend/src/features/homework/components/` (như `SubmissionHistoryModal.tsx`, `UnifiedSubmissionTimeline.tsx`, `submissionUtils.ts`) với các types mới

**Checkpoint**: Cả 3 User Stories hoạt động hoàn chỉnh, module Homework trở thành hình mẫu chuẩn (Pilot Reference) cho toàn bộ dự án.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Đảm bảo chất lượng toàn diện, dọn dẹp mã nguồn và xác minh theo tài liệu hướng dẫn

- [x] T013 Thực thi kiểm tra chất lượng mã nguồn toàn diện cho frontend (`npm run lint` và `npm run build`) tại `frontend/`
- [x] T014 Thực hiện toàn bộ các kịch bản kiểm thử đầu-cuối theo hướng dẫn trong `specs/054-openapi-type-generation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không phụ thuộc - có thể bắt đầu ngay lập tức
- **Foundational (Phase 2)**: Phụ thuộc vào hoàn tất Phase 1 - CHẶN (BLOCKS) tất cả User Stories
- **User Story 1 (Phase 3 - P1)**: Phụ thuộc vào Phase 2 hoàn tất - Cung cấp tệp `api.generated.d.ts`
- **User Story 2 (Phase 4 - P2)**: Phụ thuộc vào Phase 3 (cần tệp `api.generated.d.ts` để xây dựng helper)
- **User Story 3 (Phase 5 - P3)**: Phụ thuộc vào Phase 4 (cần helper `Schema<T>` để áp dụng pilot)
- **Polish (Phase 6)**: Phụ thuộc vào hoàn tất tất cả các User Stories

### Within Each User Story

- Đảm bảo kiểm tra tính toàn vẹn kiểu trước khi tích hợp sâu
- Hoàn thành module helper trước khi áp dụng vào feature code
- Kiểm tra độc lập từng user story trước khi chuyển sang story tiếp theo

### Parallel Opportunities

- T002 và T003 trong Phase 1 có thể thực hiện song song sau T001
- T008 trong Phase 4 có thể chuẩn bị độc lập ngay khi tệp `api.generated.d.ts` được sinh ra

---

## Parallel Example: Setup & Foundation

```bash
# Sau khi cài openapi-typescript:
Task: "Cấu hình script generate:api trong frontend/package.json" (T002)
Task: "Thêm target frontend-generate-api vào root Makefile" (T003)
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Hoàn thành Setup (T001-T003) & Foundation (T004-T005)
2. Hoàn thành User Story 1 (T006-T007): Lập trình viên có thể sinh type từ Backend qua URL
3. Hoàn thành User Story 2 (T008-T009): Lập trình viên có sẵn `Schema<T>` và `ApiPaths` để sử dụng
4. **Xác nhận MVP**: Kiểm tra IDE gợi ý và nhận diện kiểu thành công

### Incremental Delivery (User Story 3 & Polish)

5. Áp dụng chuyển đổi Pilot cho module `Homework` (T010-T012)
6. Chạy kiểm tra chất lượng `build` và `lint` (T013-T014)
7. Hoàn tất triển khai với zero regression
