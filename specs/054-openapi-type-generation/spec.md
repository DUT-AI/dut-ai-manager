# Feature Specification: Đồng bộ hóa hợp đồng API và sinh Type tự động cho Frontend từ OpenAPI Backend

**Feature Branch**: `specs/054-openapi-type-generation`  
**Created**: 2026-11-08  
**Status**: Ready for Planning  
**Input**: User description: `"generate:api": "openapi-typescript http://127.0.0.1:8000/openapi.json -o types/api.generated.d.ts" | import type { components, paths } from "./api.generated"; export type Schema<T extends keyof components["schemas"]> = components["schemas"][T]; export type ApiPaths = paths; | Tôi muốn định nghĩa schema trả về ở backend, frontend sẽ tự sinh type trả về tương ứng để thống nhất single truth`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sinh mã Type tự động từ hợp đồng Backend qua Live URL (Priority: P1)

Là một lập trình viên (frontend và full-stack), tôi muốn khi định nghĩa hoặc cập nhật các Pydantic schema tại backend FastAPI, frontend có thể tự động sinh ra các định nghĩa kiểu TypeScript tương ứng chỉ bằng một câu lệnh qua Live HTTP URL (`http://127.0.0.1:8001/api/v1/openapi.json`), để thống nhất một nguồn sự thật duy nhất (Single Source of Truth) và loại bỏ hoàn toàn việc viết tay các interface/type thủ công gây sai lệch.

**Why this priority**: Đây là năng lực cốt lõi của tính năng. Việc loại bỏ nhập liệu thủ công giúp ngăn ngừa lỗi sai lệch kiểu (type drifting), tiết kiệm thời gian phát triển và đảm bảo tính toàn vẹn dữ liệu giữa client và server.

**Independent Test**:
- Khởi động backend server cục bộ (`make backend-dev`).
- Định nghĩa hoặc chỉnh sửa một schema mới ở Backend (ví dụ: bổ sung trường dữ liệu vào một Schema DTO).
- Thực thi lệnh sinh type ở frontend (`npm run generate:api` hoặc `make frontend-generate-api`).
- Kiểm tra file type được sinh ra (`api.generated.d.ts`): kiểu dữ liệu mới phải xuất hiện đầy đủ với các thuộc tính và kiểu tương ứng.

**Acceptance Scenarios**:
1. **Given** backend FastAPI đang chạy tại cổng `8001`, **When** lập trình viên chạy lệnh sinh type ở frontend, **Then** hệ thống kết nối tới `http://127.0.0.1:8001/api/v1/openapi.json` và sinh ra file định nghĩa type TypeScript hoàn chỉnh chứa đầy đủ `components["schemas"]` và `paths`.
2. **Given** một trường dữ liệu trong schema backend bị thay đổi kiểu hoặc tên, **When** chạy lệnh sinh type, **Then** tệp type được cập nhật chính xác phản ánh thay đổi đó mà không cần can thiệp thủ công vào file `.d.ts`.
3. **Given** backend server chưa chạy hoặc cổng mạng bị chặn, **When** chạy lệnh sinh type, **Then** hệ thống báo lỗi rõ ràng hướng dẫn lập trình viên khởi động backend server trước (`make backend-dev`).

---

### User Story 2 - Sử dụng Type Helper chuẩn hóa và tương thích Envelope ApiResponse (Priority: P2)

Là một lập trình viên frontend, tôi muốn truy cập các type trả về từ Backend thông qua các helper tiện ích ngắn gọn như `Schema<"TênSchema">`, `ApiPaths`, và các helper trích xuất dữ liệu bọc bởi `ApiResponse[T]`, để có gợi ý code tự động (Autocomplete/IntelliSense) chuẩn xác, loại bỏ code bọc thủ công rườm rà và kiểm tra lỗi kiểu tĩnh tại thời điểm biên dịch.

**Why this priority**: Sinh type ra là chưa đủ; lập trình viên cần trải nghiệm sử dụng (Developer Experience) thuận tiện, dễ đọc và tích hợp trơn tru với chuẩn phong bì `ApiResponse[T]` (chứa `is_success`, `data: T`, `message`, `pagination`) mà không phải khai báo lại generic type phức tạp.

**Independent Test**:
- Trong một component hoặc hook, import `type { Schema, ApiResponseData } from '@/types/api'`.
- Gõ `Schema<` -> IDE tự động gợi ý danh sách toàn bộ các schema name hiện có từ Backend (ví dụ `Schema<"HomeworkDetailResponse">`, `Schema<"MeetingResponse">`).
- Khai báo kiểu phản hồi endpoint hoặc mutation sử dụng helper và kiểm tra TypeScript nhận diện chính xác kiểu của payload bên trong `data`.

**Acceptance Scenarios**:
1. **Given** file định nghĩa type đã được sinh, **When** lập trình viên sử dụng `Schema<"TênSchema">`, **Then** TypeScript nhận diện chính xác kiểu cấu trúc của schema đó từ `components["schemas"]`.
2. **Given** một API endpoint trả về bọc trong phong bì `ApiResponse[T]`, **When** sử dụng helper bọc/mở `ApiResponseData`, **Then** kiểu của thuộc tính `data` phản ánh chính xác schema nghiệp vụ tương ứng mà không bị `any` hay `unknown`.
3. **Given** lập trình viên nhập sai tên schema (không tồn tại trong backend), **When** TypeScript kiểm tra kiểu, **Then** IDE và trình biên dịch báo lỗi đỏ ngay lập tức.

---

### User Story 3 - Áp dụng thử nghiệm mẫu (Pilot) an toàn cho 1 Domain (Priority: P3)

Là một kỹ sư phần mềm, tôi muốn áp dụng thử nghiệm quy trình dùng type sinh tự động trên 1 domain tiêu biểu (module `Homework`), di chuyển các kiểu dữ liệu thủ công sang `Schema<T>` mà không làm gián đoạn hay ảnh hưởng tới các module còn lại của hệ thống.

**Why this priority**: Đảm bảo an toàn triển khai (Zero Regression), cung cấp một hình mẫu chuẩn hóa (Reference Implementation) để toàn bộ nhóm lập trình có thể học hỏi và áp dụng dần cho các module khác.

**Independent Test**:
- Chuyển đổi các định nghĩa kiểu trong module `Homework` sang sử dụng type sinh từ `Schema<...>`.
- Chạy toàn bộ test và build frontend (`npm run build`, `npm run lint`).
- Mọi trang màn hình và modal liên quan đến Homework (như `SubmissionHistoryModal`, `UnifiedSubmissionTimeline`, `MyHomeworkDetailPage`) hoạt động bình thường, không có lỗi kiểu.

**Acceptance Scenarios**:
1. **Given** module `Homework` được chuyển sang sử dụng generated types, **When** chạy kiểm tra chất lượng và build frontend, **Then** dự án biên dịch thành công mà không có lỗi TypeScript.
2. **Given** các module khác chưa chuyển đổi, **When** tích hợp tính năng sinh type, **Then** không gây bất kỳ tác động tiêu cực hay phá vỡ tương thích nào.

---

### Edge Cases

- **Backend server đang tắt hoặc không truy cập được**: Lệnh sinh type qua HTTP `http://127.0.0.1:8001/api/v1/openapi.json` sẽ thất bại với lỗi kết nối (`ECONNREFUSED`). Lệnh script phải đưa ra hướng dẫn rõ ràng: *"Vui lòng khởi động backend server (make backend-dev) trước khi chạy lệnh sinh type"*.
- **Schema có kiểu Generic hoặc Response Envelope**: Trong FastAPI, các schema có thể được bọc qua generic như `ApiResponse_HomeworkDetailResponse_`. Công cụ helper phải hỗ trợ cả việc lấy schema con trực tiếp (`Schema<"HomeworkDetailResponse">`) và schema phong bì.
- **Tên Schema bị trùng lặp hoặc có ký tự đặc biệt**: Khi backend có schema cùng tên hoặc schema sinh tự động từ Pydantic Generic, OpenAPI 3.1 có thể đặt tên dạng `ApiResponse[HomeworkDetailResponse]`. Cần đảm bảo `openapi-typescript` phân giải hợp lệ các định danh này thành TypeScript types an toàn.
- **Trường hợp trường dữ liệu là Optional/Nullable**: OpenAPI 3.1 ánh xạ trường `None` thành `type | null`. Hệ thống type sinh ra phải phân biệt rõ giữa trường có thể mang giá trị `null` và trường không bắt buộc (optional `?`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống Backend (FastAPI) MUST cung cấp tài liệu OpenAPI Specification (OpenAPI 3.1) đầy đủ, chính xác tại endpoint `/api/v1/openapi.json` ở cổng `8001`.
- **FR-002**: Hệ thống Frontend MUST tích hợp công cụ `openapi-typescript` để tự động chuyển đổi từ OpenAPI Specification của Backend sang tệp TypeScript definition (`frontend/src/types/api.generated.d.ts`).
- **FR-003**: Lệnh sinh type MUST sử dụng Live HTTP URL (`http://127.0.0.1:8001/api/v1/openapi.json`). Khi kết nối thất bại do server chưa chạy, script phải hiển thị hướng dẫn rõ ràng yêu cầu bật `make backend-dev`.
- **FR-004**: Frontend MUST cung cấp module type helper chuẩn hóa (`frontend/src/types/api.ts` hoặc tương đương) cung cấp:
  - `Schema<T extends keyof components["schemas"]>`: Trích xuất trực tiếp schema component từ backend.
  - `ApiPaths = paths`: Định nghĩa toàn bộ đường dẫn API của hệ thống.
  - Các helper hỗ trợ phong bì `ApiResponse[T]` (như `ApiResponseData<Path, Method>` hoặc `ApiResponseSchema<T>`) giúp trích xuất kiểu dữ liệu của trường `data` trong phản hồi chuẩn.
- **FR-005**: Hệ thống type helper MUST tương thích hoàn toàn với Hiến chương dự án (Điều V - Chuẩn phong bì `ApiResponse[T]`), bảo đảm không sinh ra kiểu `any` hoặc `unknown` cho các payload hợp lệ.
- **FR-006**: Chiến lược triển khai ban đầu MUST tuân theo mô hình **Foundation + Pilot**:
  - Thiết lập hoàn chỉnh toolchain và các script sinh type.
  - Áp dụng mẫu (Pilot) cho module `Homework`, chứng minh tính khả thi và loại bỏ type viết tay cho các schema chính của module này.
  - Giữ nguyên các module khác để đảm bảo tính an toàn (Zero Regression).
- **FR-007**: Tệp sinh type tự động (`api.generated.d.ts`) MUST được chỉ định đường dẫn cố định, không ghi đè làm mất mát mã nguồn nghiệp vụ hiện có.
- **FR-008**: Các scripts điều phối sinh type MUST được cấu hình trong `frontend/package.json` (`generate:api`) và `Makefile` ở thư mục gốc (`frontend-generate-api` / `generate-api`).

---

### Key Entities

- **OpenAPI Schema Contract**: Bản mô tả cấu trúc dữ liệu JSON Schema chuẩn OpenAPI 3.1 được xuất tại `/api/v1/openapi.json` từ FastAPI backend.
- **Generated API Definitions (`frontend/src/types/api.generated.d.ts`)**: Tệp TypeScript definition chứa toàn bộ `components["schemas"]` và `paths` được sinh tự động.
- **Contract Type Helpers (`frontend/src/types/api.ts`)**: Module chứa các tiện ích TypeScript (`Schema<T>`, `ApiPaths`, `ApiResponseData<...>`) hỗ trợ trích xuất kiểu dữ liệu cho UI components, React Query hooks và Axios network client.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các schema trả về được định nghĩa ở Backend (Pydantic / FastAPI) được tự động ánh xạ đầy đủ và chính xác sang TypeScript types khi chạy lệnh sinh type.
- **SC-002**: Lệnh sinh type hoàn thành trong thời gian dưới 5 giây khi backend server đang chạy cục bộ.
- **SC-003**: Trải nghiệm lập trình viên đạt độ chính xác 100%: IDE tự động gợi ý đầy đủ danh sách tên schema trong `Schema<"...">` và báo lỗi biên dịch tĩnh tức thì khi thuộc tính truy cập không tồn tại trong backend schema.
- **SC-004**: Không phát sinh bất kỳ lỗi biên dịch TypeScript (`tsc`) hoặc linting nào đối với toàn bộ dự án frontend khi tích hợp công cụ và di chuyển module thử nghiệm (Homework).
- **SC-005**: 100% các kiểu dữ liệu của module thử nghiệm (Homework) được thống nhất với backend schema, loại bỏ hoàn toàn tình trạng lệch kiểu (type drifting).

---

## Assumptions

- Backend đang sử dụng FastAPI với Pydantic v2 và cấu trúc `openapi_url` tại `/api/v1/openapi.json` trên cổng `8001`.
- Lập trình viên chạy lệnh sinh type khi backend server đang hoạt động (`make backend-dev`).
- Các endpoint API có khai báo `response_model` hoặc type annotations rõ ràng để OpenAPI trích xuất được schema.
- Tệp sinh tự động `api.generated.d.ts` được đặt trong `frontend/src/types/` và quản lý phiên bản trong Git để đảm bảo tính sẵn sàng cho CI/CD.
