# Research: Clean Architecture Ports & Adapters for Homework Module

**Feature**: `071-architecture-redesign`  
**Date**: 2026-11-16  
**Status**: Completed  

---

## 1. Research Objectives
Xác định giải pháp kiến trúc để tái cấu trúc module `backend/app/homework` thành hình mẫu Clean Architecture chuẩn mực:
1. **Ports & Adapters (Hexagonal Architecture)**: Tách rời Use Case khỏi cài đặt cụ thể của SQLAlchemy thông qua Abstract Repository Ports.
2. **In-Memory Fake Repositories**: Xây dựng kho lưu trữ giả lập trên RAM để kiểm thử Use Case mà không phụ thuộc vào `MagicMock` hay Database thật.
3. **Dependency Injection với Dishka**: Cấu hình Dishka để nạp Repository thông qua Port Interface, cho phép hoán đổi adapter linh hoạt giữa production và test.
4. **Giảm thiểu Fragile Tests**: Chuyển đổi các bài unit test dễ vỡ thành các bài test hướng hành vi (Behavior-driven) bền vững.

---

## 2. Decisions, Rationales & Alternatives

### Decision 1: Vị trí đặt Repository Ports (`backend/app/homework/domain/ports/`)
- **Decision**: 
  - Khai báo các abstract classes kế thừa từ `abc.ABC` trong package `backend/app/homework/domain/ports/`:
    - `HomeworkRepositoryPort`
    - `HomeworkSubmissionRepositoryPort`
    - `HomeworkAssigneeRepositoryPort`
- **Rationale**:
  - Trong Clean Architecture và DDD, Repository Interface là một **Outbound Port (Driven Port)** thuộc quyền sở hữu của Domain / Application. Đặt trong `domain/ports/` đảm bảo tính độc lập tuyệt đối: không phụ thuộc vào SQLAlchemy, HTTP hay bất kỳ third-party nào.
  - Cả Tầng Application (Use Case) và Tầng Infrastructure (SQLAlchemy / InMemory) đều có thể import từ `domain/ports/` mà không gây ra circular dependency.
- **Alternatives Considered**:
  - *Đặt trong `infrastructure/ports.py`*: Bị bác bỏ vì vi phạm Dependency Inversion Principle (DIP). Domain và Application không được import từ Infrastructure.
  - *Đặt trong `application/ports.py`*: Khả thi, nhưng đặt trong `domain/ports/` giúp Entity và Ports gắn kết chặt chẽ hơn trong cùng một Bounded Context.

---

### Decision 2: Thiết kế In-Memory Fake Repositories (`backend/app/homework/infrastructure/in_memory/`)
- **Decision**:
  - Tạo các In-Memory Repositories thực thi 100% hợp đồng của Port:
    - `InMemoryHomeworkRepository(HomeworkRepositoryPort)`
    - `InMemoryHomeworkSubmissionRepository(HomeworkSubmissionRepositoryPort)`
    - `InMemoryHomeworkAssigneeRepository(HomeworkAssigneeRepositoryPort)`
  - Dữ liệu được lưu trong các cấu trúc Python thuần túy: `dict[int, HomeworkEntity]`, `list[HomeworkSubmission]`, `dict[tuple[int, int], datetime]`.
- **Rationale**:
  - Thay thế hoàn toàn việc phải mock chi tiết từng phương thức bằng `MagicMock()` trong Unit Tests.
  - Khi Use Case gọi `repo.save(hw)` hoặc `repo.add_submission(sub)`, dữ liệu thực sự được lưu vào RAM. Khi gọi `repo.get_by_id(id)` hoặc `repo.get_submissions_by_user()`, dữ liệu thực sự được trả về.
  - Giúp phát hiện ngay lỗi logic dữ liệu, kiểm tra được luồng CRUD hoàn chỉnh mà tốc độ chạy vẫn đạt hàng nghìn test/giây.
- **Alternatives Considered**:
  - *Sử dụng SQLite in-memory*: Vẫn cần SQLAlchemy Session, schema migrations, và engine connection, chạy chậm hơn 10x-50x so với pure Python dict và phức tạp khi setup.
  - *Tiếp tục dùng MagicMock*: Bị bác bỏ vì là nguyên nhân gây ra Mocking Hell và test dễ vỡ.

---

### Decision 3: Tương thích ngược với SQLAlchemy Repositories hiện tại
- **Decision**:
  - Cho các SQLAlchemy Repositories hiện có (`HomeworkRepository`, `HomeworkSubmissionRepository`, `HomeworkAssigneeRepository`) kế thừa trực tiếp từ các Ports tương ứng:
    ```python
    class HomeworkRepository(HomeworkRepositoryPort):
        def __init__(self, session: Session): ...
    ```
- **Rationale**:
  - Tuân thủ Liskov Substitution Principle (LSP).
  - Không phá vỡ bất kỳ code controller hay use case cũ nào đang chạy trong lúc chuyển đổi.
  - Đảm bảo 100% tương thích ngược với Dishka Provider và hệ sinh thái hiện tại.
- **Alternatives Considered**:
  - *Đổi tên `HomeworkRepository` thành `SqlAlchemyHomeworkRepository` ngay lập tức*: Gây xáo trộn lớn ở nhiều file import. Cách tốt hơn là tạo alias hoặc kế thừa trước, refactor dần theo Strangler Fig.

---

### Decision 4: Cấu hình Dishka Dependency Injection
- **Decision**:
  - Trong `backend/app/homework/providers.py`, khai báo provider cung cấp Repository thông qua Port:
    ```python
    @provide
    def get_homework_repo(self, session: Session) -> HomeworkRepositoryPort:
        return HomeworkRepository(session)
    ```
  - Trong tests hoặc containers kiểm thử, có thể dễ dàng override provider với `InMemoryHomeworkRepository`.
- **Rationale**:
  - Use Cases có thể inject `FromDishka[HomeworkRepositoryPort]` thay vì phụ thuộc vào concrete class.
  - Tách rời hoàn toàn presentation/application khỏi công nghệ lưu trữ.

---

## 3. Best Practices & Guidelines
1. **Zero Mock on Entities**: Tuyệt đối không mock `Homework` hay `HomeworkSubmission` bằng `MagicMock(spec=...)`. Luôn dùng instance thật.
2. **Behavior Verification Over Call Count**: Test tập trung vào: "Sau khi thực thi Use Case, dữ liệu trong Repository thay đổi thế nào và Event nào được bắn ra", thay vì kiểm tra "hàm này được gọi mấy lần với tham số gì".
3. **Continuous Regression Testing**: Chạy toàn bộ 455 tests backend để đảm bảo không có bất kỳ regression nào trong quá trình chuyển đổi sang Ports & Adapters.
