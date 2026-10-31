# Research: Phân tích & Giải pháp Loại bỏ `Any` và `getattr()` trong Meeting Domain & Schemas

## 1. Nguồn Gốc & Phân Tích Kỹ Thuật

### Câu hỏi đặt ra:
> *"Có phải do thuộc tính `participants: list[MeetingParticipant] = Field(default_factory=list)` của Meeting không?"*

### Trả lời & Phân tích chuyên sâu:
1. **Sự liên đới từ thuộc tính `participants`**:
   - `Meeting` là Aggregate Root trong Domain-Driven Design (DDD). Trong thiết kế ban đầu, `Meeting` chứa toàn bộ người tham gia dưới dạng một danh sách duy nhất: `participants: list[MeetingParticipant]`.
   - Vì danh sách này phẳng và chứa lẫn lộn cả Trainer và Trainee, nên ở tầng DTO (khi chuyển đổi sang `MeetingResponse` hay `MeetingDetailResponse`), lập trình viên buộc phải duyệt qua danh sách và kiểm tra từng phần tử.
   - Khi chưa có property `trainers` / `trainees` rõ ràng trên Domain Entity, tầng Schemas phải tự kiểm tra runtime xem đối tượng có thuộc tính `role` hay không, dẫn đến `getattr(p, "role", ParticipantRole.TRAINEE)`.

2. **Nguyên nhân chính và sâu xa hơn**:
   - **Tầng Schemas không coi Domain Entities là Strong Contracts**:
     - Các mapper DTO được viết với chữ ký: `def from_domain(cls, e: Any) -> ...`.
     - Khi nhận `e: Any`, trình phân tích tĩnh (linter, MyPy) không thể biết `e` có thuộc tính gì. Để tránh `AttributeError`, lập trình viên đã viết `getattr(e, "field", default)` cho hầu như mọi trường.
   - **Lẫn lộn giữa ORM Model và Domain Entity**:
     - Đôi khi Use Case hoặc Controller cũ truyền trực tiếp SQLAlchemy ORM Model (`MeetingModel`, `MeetingParticipantModel`, `MeetingEvaluationModel`) vào Schema thay vì qua Domain Entity. Vì ORM Model có quan hệ lazy loading (như `p.user`) có thể trả về `None` hoặc chưa được nạp, dẫn đến việc dùng `getattr(p, "user", None)` và `getattr(p_user, "name", None)`.
   - **Vi phạm Hiến pháp Điều XIV (No Fake Optionals & Fail-Fast Parameter Contracts)**:
     - Dùng `getattr` với giá trị fallback ngầm (e.g. `getattr(s, "score", 0)`, `getattr(e, "average_score", 0.0)`) che giấu các lỗi truy vấn hoặc dữ liệu rỗng, thay vì fail-fast hoặc dựa trên domain invariant.

---

## 2. Các Quyết định Kỹ thuật (Decisions & Trade-offs)

### Quyết định 1: Định kiểu tường minh 100% trong chữ ký `from_domain`
- **Lựa chọn**: Đổi toàn bộ `e: Any` thành Domain Entity tương ứng:
  - `MeetingResponse.from_domain(cls, m: DomainMeeting) -> MeetingResponse`
  - `MeetingDetailResponse.from_domain(cls, m: DomainMeeting) -> MeetingDetailResponse`
  - `ParticipantResponse.from_domain(cls, p: MeetingParticipant) -> ParticipantResponse`
  - `MeetingOverallEvaluationResponse.from_domain(cls, e: MeetingOverallEvaluation) -> MeetingOverallEvaluationResponse`
  - `MeetingEvaluationResponse.from_domain(cls, e: MeetingEvaluation, is_owner: bool = False) -> MeetingEvaluationResponse`
- **Lý do**:
  - Tận dụng sức mạnh của Pydantic V2 và Python 3.12 type hinting.
  - IDE và linter phát hiện ngay lỗi chính tả hoặc thiếu trường khi biên dịch, không cần chờ đến lúc chạy API.

### Quyết định 2: Tối ưu Aggregate Root `Meeting`
- **Lựa chọn**:
  - Giữ `participants: list[MeetingParticipant]` làm Single Source of Truth cho toàn bộ danh sách thành viên trong Aggregate Root `Meeting`.
  - Giữ và tối ưu hóa 2 property:
    - `@property def trainers(self) -> list[MeetingParticipant]: return [p for p in self.participants if not p.is_deleted and p.role == ParticipantRole.TRAINER]`
    - `@property def trainees(self) -> list[MeetingParticipant]: return [p for p in self.participants if not p.is_deleted and p.role == ParticipantRole.TRAINEE]`
  - Loại bỏ hoàn toàn `getattr(p, "is_deleted", False)` trong `meeting.py`, vì `MeetingParticipant` kế thừa `BaseEntity` vốn đã định nghĩa trường `is_deleted: bool = False`.

### Quyết định 3: Tách bạch Pydantic Model Validator và Domain Mapper
- **Lựa chọn**:
  - Trong `participant_schemas.py`: Validator `@model_validator(mode="before")` chỉ chịu trách nhiệm parse các dictionary/JSON payload gửi từ client (nếu có), không can thiệp vào Domain Entity.
  - Khi map từ Domain Entity, bắt buộc sử dụng `ParticipantResponse.from_domain(p: MeetingParticipant)` với thuộc tính trực tiếp (`p.id`, `p.user_id`, `p.role`, `p.user.name`...).

### Quyết định 4: Loại bỏ toàn bộ `getattr` trong `evaluation_schemas.py`
- **Lựa chọn**:
  - `MeetingOverallEvaluation` và `MeetingEvaluation` là các Domain Entities đã có sẵn cấu trúc đầy đủ (`scores: list[EvaluationScoreItem]`, `trainer: UserRef | None`, `reviewer: UserRef | None`).
  - Thay thế toàn bộ `getattr(e, ...)` và `getattr(s, ...)` bằng truy cập thuộc tính trực tiếp `e.scores`, `s.criteria_code`, `s.score`, `e.trainer.name` (có kiểm tra `if e.trainer is not None:`).
