# API Contract: Homework Submission Webhook

**Endpoint**: `POST /api/v1/homeworks/webhook/submission`  
**Tags**: `homeworks`  
**Security**: Header `X-Webhook-Secret`  

---

## 1. Request Headers

| Header | Type | Required | Description |
|---|---|---|---|
| `Content-Type` | `string` | Yes | Must be `application/json` |
| `X-Webhook-Secret` | `string` | Yes | Secret token shared between Quiz API and DUT AI Manager |

---

## 2. Request Body (`HomeworkSubmissionWebhookIn`)

### 2.1 Coding Submission Example
```json
{
  "lesson_slug": "python-basic-lesson-01",
  "user_id": 42,
  "type": "CODING",
  "submitted_at": "2026-11-16T14:30:00Z",
  "is_passed": true,
  "exercise_id": "ex-01-loops",
  "exercise_title": "Vòng lặp For",
  "submission_id": "sub_987654",
  "attempt_number": 2,
  "score": 10.0,
  "original_filename": "solution.py",
  "details": {
    "language": "python",
    "code": "for i in range(10): print(i)",
    "pass_count": 5,
    "total_count": 5,
    "test_cases_passed": 5,
    "total_test_cases": 5
  }
}
```

### 2.2 Game Quiz Submission Example
```json
{
  "lesson_slug": "python-basic-lesson-01",
  "user_id": 42,
  "type": "GAME",
  "submitted_at": "2026-11-16T15:00:00Z",
  "is_passed": true,
  "attempt_number": 1,
  "score": 8.5,
  "details": {
    "total_questions": 10,
    "correct_count": 8,
    "duration_seconds": 120
  }
}
```

---

## 3. Response Structure (`ApiResponse[HomeworkWebhookResponse]`)

### 3.1 HTTP 200 OK — Successfully Recorded
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "status": "recorded",
    "message": null,
    "reason": null,
    "submission_id": 1024,
    "homework_id": 15,
    "user_id": 42,
    "exercise_id": "ex-01-loops"
  }
}
```

### 3.2 HTTP 200 OK — Updated Existing Submission
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "status": "updated",
    "message": null,
    "reason": null,
    "submission_id": 1024,
    "homework_id": 15,
    "user_id": 42,
    "exercise_id": "ex-01-loops"
  }
}
```

### 3.3 HTTP 200 OK — Ignored (External User or Unmatched Slug)
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "status": "ignored",
    "message": null,
    "reason": "External user (id >= 1,000,000)",
    "submission_id": null,
    "homework_id": null,
    "user_id": null,
    "exercise_id": null
  }
}
```

### 3.4 HTTP 401 Unauthorized — Invalid or Missing Secret
```json
{
  "detail": "Invalid or missing X-Webhook-Secret header"
}
```

### 3.5 HTTP 422 Unprocessable Entity — Schema Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "type"],
      "msg": "Invalid submission type: INVALID. Must be CODING or GAME",
      "type": "value_error"
    }
  ]
}
```
