# Data Model & Fixture Topology: In-Memory Fake Testing

**Feature**: `072-homework-inmemory-test-migration`  
**Date**: 2026-11-16  

---

## 1. Test Fixtures Topology

Sơ đồ quan hệ dữ liệu trong bộ nhớ RAM phục vụ kiểm thử Use Cases:

```
+---------------------------------------------------------------------------------+
|                               Memory Fixture Space                              |
|                                                                                 |
|  +-----------------------------+         +-----------------------------------+  |
|  | InMemoryHomeworkRepository  |         | InMemoryHomeworkAssigneeRepository|  |
|  | - _storage: dict[id, HW]    |◄──┐     | - _assignees: dict[(hw,user), dt] |  |
|  | - _next_id: int             |   │     | - _hw_info: dict[hw, (title...)]  |  |
|  +-----------------------------+   │     | - _user_info: dict[user, (name..)]|  |
|                                    │     +-----------------------------------+  |
|                                    │                       ▲                    |
|                                    │                       │                    |
|                        +-----------┴-----------+           │                    |
|                        |   Homework Use Case   |───────────┘                    |
|                        +-----------┬-----------+                                |
|                                    │                                            |
|                                    ▼                                            |
|                  +------------------------------------+                         |
|                  |InMemoryHomeworkSubmissionRepository|                         |
|                  | - _submissions: dict[id, Sub]      |                         |
|                  | - _next_id: int                    |                         |
|                  +------------------------------------+                         |
+---------------------------------------------------------------------------------+
```

---

## 2. Shared Test Harness Entities

### 2.1 FakeQuizApiClient
- **Mục đích**: Thay thế `QuizApiClient` trong kiểm thử đơn vị mà không gọi mạng HTTP.
- **Dữ liệu lưu trữ**: `_exercises: dict[str, list[dict]]` (mapping từ lesson `slug` sang danh sách bài tập con).
- **Phương thức**:
  - `set_lesson_exercises(slug: str, exercises: list[dict]) -> None`
  - `get_lesson_exercises(slug: str) -> list[dict]` (async)
  - `get_lesson_metadata(slug: str) -> dict[str, Any]` (async)

### 2.2 SpyEventBus
- **Mục đích**: Thu thập và kiểm tra các Domain Event phát ra từ Use Case mà không gây side-effect ra ngoài.
- **Dữ liệu lưu trữ**: `published_events: list[DomainEvent]`
- **Phương thức**:
  - `publish(event: DomainEvent) -> None` (async)
  - `clear() -> None`
  - `get_events_of_type(event_type: type[T]) -> list[T]`

---

## 3. Data Seeding Conventions

Khi viết test case, dữ liệu được nạp vào InMemory Repositories theo quy chuẩn:

| Khái niệm | Kiểu dữ liệu | Quy chuẩn giá trị |
| :--- | :--- | :--- |
| `Homework` | `HomeworkEntity` | `id` dương, `title` rõ ràng, `slug` chuẩn hóa lowercase, `requires_coding` và `requires_game` minh thị |
| `Assignee` | `AssigneeUserInfo` | `user_id` định danh duy nhất, `deadline` timezone-aware UTC (`ensure_utc(...)`) |
| `Submission` | `HomeworkSubmission` | Sử dụng Factory Method `create_coding(...)` hoặc `create_game(...)`, `submitted_at` UTC |
