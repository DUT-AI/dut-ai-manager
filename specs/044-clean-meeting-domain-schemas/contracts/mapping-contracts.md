# Mapping Contracts: Domain to Schema Specifications

## 1. Domain Entities to Schema Signatures

| Source Domain Entity | Target Schema DTO | Method Signature | Ghi chú |
| :--- | :--- | :--- | :--- |
| `Meeting` | `MeetingResponse` | `from_domain(cls, m: DomainMeeting) -> MeetingResponse` | Không dùng `getattr()`. Bóc `trainers` từ `m.trainers`. |
| `Meeting` | `MeetingDetailResponse` | `from_domain(cls, m: DomainMeeting) -> MeetingDetailResponse` | Tách trực tiếp `trainers` và `trainees`. |
| `MeetingParticipant` | `ParticipantResponse` | `from_domain(cls, p: MeetingParticipant) -> ParticipantResponse` | Thay thế `p: Any` bằng `MeetingParticipant`. |
| `MeetingOverallEvaluation` | `MeetingOverallEvaluationResponse` | `from_domain(cls, e: MeetingOverallEvaluation) -> MeetingOverallEvaluationResponse` | Truy cập trực tiếp `e.scores`, `e.trainer`. |
| `MeetingEvaluation` | `MeetingEvaluationResponse` | `from_domain(cls, e: MeetingEvaluation, is_owner: bool = False) -> MeetingEvaluationResponse` | Truy cập trực tiếp `e.scores`, `e.reviewer`. |

## 2. Invariants & Rules
1. **Zero `getattr` rule**: Tuyệt đối không sử dụng `getattr(entity, ...)` cho bất kỳ trường nào đã được định nghĩa trong Domain Entity hoặc BaseEntity (`id`, `created_at`, `updated_at`, `is_deleted`).
2. **Explicit Null Safety**: Chỉ dùng `if entity.field is not None:` khi trường đó là `Optional` (`| None`), tuyệt đối không dùng `getattr(entity, "field", None)`.
3. **No `Any` Ingestion**: Các classmethod `from_domain` từ chối `Any` và yêu cầu chính xác type hint của Domain Entity tương ứng.
