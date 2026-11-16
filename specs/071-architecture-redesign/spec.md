# Feature Specification: System Architecture Redesign & Clean Architecture Blueprint

**Feature Branch**: `071-architecture-redesign`  
**Created**: 2026-11-16  
**Status**: Draft  
**Input**: Yêu cầu người dùng: "Nếu đập xây lại hoàn toàn thì tôi cần phải làm gì để xây dựng hệ thống chuyên nghiệp về code và kiến trúc?"

---

## Background & Motivation

Qua quá trình bảo trì và phát triển hệ thống `dut-ai-manager`, các vấn đề nợ kỹ thuật (technical debt) lớn nhất thường xuyên phát sinh từ:
1. **Dính chặt vào Database và Repository (Database-Coupled Logic)**: Các Use Cases phụ thuộc vào chi tiết cài đặt của Repository và SQLAlchemy, khiến việc kiểm thử bị rơi vào "Địa ngục Mock" (Mocking Hell), kiểm thử dễ vỡ (brittle tests) khi chỉ cần sửa câu lệnh truy vấn.
2. **Logic nghiệp vụ phân mảnh (Anemic Domain & Logic Leakage)**: Phán đoán trạng thái bài tập, điểm danh, vi phạm nằm rải rác giữa SQL query, Use Case và Helper thay vì tập trung tại một nguồn chân lý duy nhất (SSOT).
3. **Lỏng lẻo kiểu dữ liệu (Dynamic Dictionaries & Duck-Typing)**: Việc sử dụng `dict[str, Any]` và các hàm phòng thủ thời gian chạy (`isinstance`, `getattr`) che giấu lỗi schema, gây khó khăn cho việc bảo trì dài hạn.

Bản đặc tả này xác lập **Khuôn mẫu Kiến trúc Chuẩn (Target Architecture Blueprint)** cho một hệ thống phần mềm chuyên nghiệp, có khả năng mở rộng cao, dễ kiểm thử và độc lập hoàn toàn giữa nghiệp vụ và công nghệ lưu trữ.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pure Domain Modeling & Zero-IO Business Logic (Priority: P1) 🎯 MVP

Là một Kỹ sư phần mềm phát triển hệ sinh thái quản lý,  
Tôi muốn toàn bộ quy tắc nghiệp vụ cốt lõi (đánh giá bài tập, tính toán vi phạm, chuyển đổi trạng thái người dùng) được đóng gói bên trong các Thực thể Nghiệp vụ Thuần túy (Pure Domain Entities & Aggregate Roots),  
Để các quy tắc này có thể được phát triển và kiểm thử độc lập 100% mà không cần kết nối cơ sở dữ liệu hay thư viện ngoài.

**Why this priority**: Đây là nền tảng cốt lõi của Clean Architecture. Nếu nghiệp vụ không sạch, toàn bộ hệ thống phía trên sẽ tiếp tục bị rò rỉ chi tiết kỹ thuật và phụ thuộc chặt vào database.

**Independent Test**: Có thể kiểm thử 100% các kịch bản đánh giá nộp bài, phân loại trạng thái bằng các bài test chạy trực tiếp trên RAM, không sử dụng Mock, không kết nối Database, thời gian chạy dưới 1 mili-giây.

**Acceptance Scenarios**:
1. **Given** một đề bài tập có yêu cầu coding và game, **When** một học viên nộp đủ các bài tập con trước hạn, **Then** Entity tự đánh giá trạng thái hoàn thành hợp lệ mà không cần gọi bất kỳ hàm kiểm tra phụ nào.
2. **Given** danh sách bài nộp rỗng hoặc nộp thiếu phần coding, **When** thực hiện đánh giá, **Then** Entity trả về danh mục còn thiếu chính xác theo đúng Single Source of Truth.
3. **Given** một quy tắc nghiệp vụ thay đổi, **When** cập nhật Entity, **Then** các tầng Controller, Database Model không bị ảnh hưởng.

---

### User Story 2 - Ports & Adapters (Hexagonal Architecture) with In-Memory Test Fixtures (Priority: P2)

Là một Kỹ sư kiểm thử và bảo trì hệ thống,  
Tôi muốn Tầng Ứng dụng (Application Layer / Use Cases) chỉ giao tiếp với Cơ sở dữ liệu thông qua các Cổng giao tiếp trừu tượng (Ports / Abstract Interfaces),  
Để trong môi trường kiểm thử, hệ thống có thể thay thế Database bằng Kho lưu trữ trong bộ nhớ (In-Memory Fake Repository) giúp loại bỏ hoàn toàn việc mock từng hàm riêng lẻ.

**Why this priority**: Giải quyết dứt điểm vấn nạn "Mocking Hell". Khi có Fake Repository, Use Case có thể chạy trơn tru như thật trong bộ nhớ RAM, giúp test bền vững và phản ánh đúng hành vi người dùng.

**Independent Test**: Viết Use Case test tương tác thêm/sửa/xóa bài tập thông qua `InMemoryHomeworkRepository`, xác nhận test chạy thành công mà không sử dụng bất kỳ câu lệnh `MagicMock()` nào cho Repository.

**Acceptance Scenarios**:
1. **Given** một Use Case cần nạp dữ liệu từ hệ thống lưu trữ, **When** chạy trong môi trường kiểm thử, **Then** Use Case nhận một Fake Repository lưu trữ bằng cấu trúc `dict`/`list` trong RAM.
2. **Given** cấu trúc câu lệnh truy vấn SQL trong Infrastructure bị thay đổi hoặc tối ưu hóa chỉ mục, **When** chạy lại Use Case Unit Tests, **Then** toàn bộ các bài test vẫn vượt qua 100% không bị vỡ.
3. **Given** một hệ cơ sở dữ liệu mới (ví dụ chuyển từ PostgreSQL sang lưu trữ khác), **When** triển khai Adapter mới, **Then** mã nguồn tại tầng Application và Domain hoàn toàn không phải sửa đổi một dòng nào.

---

### User Story 3 - Thin Orchestrator Use Cases & Strict Data Flow (Priority: P3)

Là một Kiến trúc sư Hệ thống,  
Tôi muốn mỗi Use Case là một Nhạc trưởng Tinh gọn (Thin Orchestrator) với duy nhất một phương thức thực thi công khai và luồng dữ liệu định kiểu tĩnh tuyệt đối từ API đến Persistence,  
Để luồng đi của dữ liệu luôn minh bạch, dễ theo dõi vết và không có bất kỳ logic nghiệp vụ nào bị "thất thoát" ra ngoài Domain.

**Why this priority**: Đảm bảo tính nhất quán trong toàn bộ dự án, tránh hiện tượng Use Case biến thành "God Object" chứa hàng trăm dòng if-else và logic phức tạp.

**Independent Test**: Kiểm tra cấu trúc từng file Use Case: mỗi file chỉ có duy nhất 1 class, 1 hàm `execute()`, tiếp nhận DTO định kiểu mạnh, ủy quyền cho Aggregate Root và phát Domain Event nếu có thay đổi trạng thái.

**Acceptance Scenarios**:
1. **Given** một yêu cầu cập nhật trạng thái từ Client, **When** đi qua Use Case, **Then** Use Case chỉ làm nhiệm vụ: Nạp Aggregate Root -> Gọi hàm trên Aggregate Root -> Lưu Aggregate Root -> Trả về Read DTO.
2. **Given** dữ liệu trả về cho Client hoặc nhận từ bên thứ ba (Webhook), **When** kiểm tra kiểu dữ liệu, **Then** không tồn tại bất kỳ kiểu từ điển thô (`dict[str, Any]`) hay thao tác duck-typing (`getattr`).
3. **Given** một tác vụ phụ như gửi thông báo Discord hay Zalo, **When** nghiệp vụ chính hoàn thành, **Then** tác vụ phụ được xử lý bất đồng bộ thông qua Event Bus mà không khóa phiên làm việc chính.

---

## Edge Cases

- **Xử lý Xung đột Phiên bản / Đồng thời (Concurrency Conflict)**: Khi hai người dùng cùng thao tác cập nhật một thực thể tại cùng một thời điểm, Aggregate Root kiểm tra phiên bản (Optimistic Locking) và từ chối cập nhật xung đột một cách an toàn.
- **Xử lý Thiếu dữ liệu Phụ thuộc (Missing Dependency Contract)**: Khi khởi tạo Use Case hoặc Repository, nếu thiếu bất kỳ collaborator bắt buộc nào, hệ thống phải báo lỗi ngay tại thời điểm khởi tạo (Fail-Fast), cấm tự động gán giá trị mặc định ảo.
- **Trạng thái Database không phản hồi (Database Outage / Timeout)**: Các tác vụ nền và webhook phải có cơ chế Retry có lũy kế thời gian chờ (Exponential Backoff) và lưu vết trạng thái idempotent để không nhân bản dữ liệu.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI phân tách kiến trúc thành 4 tầng ranh giới bất biến: `Domain` (Nghiệp vụ thuần), `Application` (Điều phối use cases), `Infrastructure` (Lưu trữ & Dịch vụ ngoài), `Presentation` (API endpoints & Schemas).
- **FR-002**: Tầng `Domain` KHÔNG ĐƯỢC PHÉP phụ thuộc vào bất kỳ thư viện framework, database (SQLAlchemy), hoặc HTTP client nào.
- **FR-003**: Tất cả các quy tắc phán đoán nghiệp vụ (hoàn thành bài, đủ điều kiện điểm danh, phát sinh vi phạm) PHẢI nằm trọn vẹn trong Aggregate Root / Domain Entity, đóng vai trò là Nguồn chân lý duy nhất (SSOT).
- **FR-004**: Tầng `Application` PHẢI định nghĩa các Interfaces/Ports (Abstract Base Classes) cho mọi thao tác đọc/ghi dữ liệu; Tầng `Infrastructure` chịu trách nhiệm cài đặt cụ thể các Interfaces này.
- **FR-005**: Hệ thống PHẢI cung cấp bộ `InMemoryRepository` (Fake Repositories) cho toàn bộ các bài Unit Test tầng Application, loại bỏ hoàn toàn việc sử dụng `MagicMock` giả lập dữ liệu thực thể.
- **FR-006**: Tất cả dữ liệu đầu vào và đầu ra của hệ thống PHẢI được định kiểu tĩnh tường minh thông qua các Value Objects và DTOs bất biến; nghiêm cấm việc dùng `dict[str, Any]` hoặc duck-typing `getattr`/`hasattr`.
- **FR-007**: Mọi tác vụ thứ cấp (thông báo Zalo, Discord, email, tính điểm cộng) PHẢI được tách rời khỏi giao dịch chính thông qua Cơ chế Sự kiện Miền (Domain Events & Asynchronous Event Handlers).

---

### Key Entities

- **Domain Entity / Aggregate Root**: Đại diện cho thực thể nghiệp vụ có danh tính (ID), chứa toàn bộ trạng thái và phương thức nghiệp vụ đảm bảo tính toàn vẹn dữ liệu (Invariant Enforcement).
- **Value Object**: Đối tượng định kiểu giá trị, bất biến (frozen), định danh bằng giá trị của các thuộc tính (ví dụ: `Deadline`, `SubmissionDetails`, `TimeRange`).
- **Repository Port**: Hợp đồng giao tiếp trừu tượng khai báo các thao tác lưu trữ và tìm kiếm thực thể (ví dụ: `HomeworkRepositoryPort`).
- **InMemory Fake Repository**: Cài đặt giả lập của Repository Port sử dụng cấu trúc dữ liệu trong bộ nhớ RAM phục vụ kiểm thử nhanh và ổn định.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% logic nghiệp vụ cốt lõi được kiểm thử tự động mà không cần kết nối cơ sở dữ liệu thật hoặc môi trường mạng.
- **SC-002**: Toàn bộ bộ kiểm thử Unit Tests của hệ thống chạy hoàn thành trong thời gian dưới 5 giây.
- **SC-003**: 0% các bài test Use Case phụ thuộc vào `MagicMock` cho các phương thức truy vấn cơ sở dữ liệu.
- **SC-004**: Tỷ lệ lỗi kiểm thử do thay đổi câu lệnh truy vấn nội bộ của Repository (False Positive Failures) giảm về 0%.
- **SC-005**: 100% giao diện API được định kiểu tĩnh thông qua Schemas/DTOs tường minh, không có cảnh báo linter về kiểu dữ liệu động.

---

## Assumptions

- Ngôn ngữ triển khai tiếp tục là Python hiện đại (3.12+) với hệ sinh thái Pydantic v2 và Dependency Injection chuẩn mực.
- Hệ thống áp dụng Chiến lược Chuyển đổi Dần dần (Strangler Fig Pattern) cho từng Bounded Context thay vì dừng toàn bộ hệ thống để viết lại cùng lúc.
- Các nhà phát triển tuân thủ kỷ luật Kiểm thử hướng hành vi (TDD / BDD) và sử dụng hợp đồng dữ liệu tĩnh.
