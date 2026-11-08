# Feature Specification: Chuẩn hóa Schema và Metadata cho Homework Submission (Coding & Game) - Clean & Strict

**Feature Identifier**: `056-standardize-submission-metadata`  
**Created Date**: 2026-11-08  
**Status**: APPROVED  
**Architecture Rule**: **Clean & Strict - Xóa hoàn toàn `details: dict[str, Any]` thô**

---

## 1. Bối cảnh & Vấn đề

Bảng `homework_submissions` trong CSDL lưu trữ trường `details` kiểu JSON không có schema kiểm soát. Khi trả về API, DTO `HomeworkSubmissionDetailResponse` khai báo `details: dict[str, Any]`, biến OpenAPI thành `{ [key: string]: unknown }`.

Frontend buộc phải viết các hàm phòng thủ, fallback 3-4 tầng (`normalizeSubmission`) để đoán xem một trường nằm ở đâu (`score` hay `final_score`, `submission_id` hay `session_id`).

---

## 2. Mục tiêu (Goals)

1. **Xóa sổ hoàn toàn `details: dict[str, Any]` vô danh** trong DTO phản hồi API.
2. **Định nghĩa 2 Pydantic schemas có kiểu tường minh**:
   - `CodingSubmissionDetails` dành riêng cho bài nộp Coding.
   - `GameSubmissionDetails` dành riêng cho bài nộp Game Quiz.
3. **Áp dụng Discriminated Union cho trường `details`**:
   `details: CodingSubmissionDetails | GameSubmissionDetails`
4. **Đồng bộ tự động sang TypeScript**:
   Tạo ra kiểu TypeScript an toàn 100%, cho phép Frontend switch-case theo `submission_type` để truy cập các thuộc tính mà không cần fallback.
5. **Dọn dẹp Frontend**:
   Rút gọn và làm sạch hàm `normalizeSubmission` trong `submissionUtils.ts`.

---

## 3. Đặc tả Hợp đồng Dữ liệu (Data Contracts)

### 3.1. CodingSubmissionDetails
```python
class CodingScoreDetail(BaseModel):
    criterion: str | None = None
    status: bool = True
    score: float | None = None
    message: str | None = None

class CodingSubmissionDetails(BaseModel):
    submission_id: str | None = None
    original_filename: str | None = None
    status: str | None = None
    score_details: list[dict[str, Any]] | list[CodingScoreDetail] | None = None
    source: str = "webhook"  # "webhook" | "manual_sync"
```

### 3.2. GameSubmissionDetails
```python
class GameSubmissionDetails(BaseModel):
    session_id: str | None = None
    final_score: float | None = None
    gold: int = 0
    total_questions: int = 0
    correct_count: int = 0
    attempt_count: int = 1
    source: str = "webhook"  # "webhook" | "manual_sync"
```

### 3.3. HomeworkSubmissionDetailResponse
```python
class HomeworkSubmissionDetailResponse(BaseModel):
    id: int
    homework_id: int
    user_id: int
    submission_type: SubmissionType  # "CODING" | "GAME"
    exercise_id: str | None = None
    exercise_title: str | None = None
    score: float | None = None
    attempt_number: int = 1
    submitted_at: datetime | None = None
    is_passed: bool = True
    # BẮT BUỘC: details có kiểu tường minh, không dùng dict vô danh
    details: CodingSubmissionDetails | GameSubmissionDetails
    created_at: datetime | None = None
```
