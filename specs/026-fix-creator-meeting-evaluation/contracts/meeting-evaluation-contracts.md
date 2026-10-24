# API & Interface Contracts: Đánh giá buổi sinh hoạt

**Feature**: `026-fix-creator-meeting-evaluation`  
**Date**: 2026-10-24  
**Status**: Completed  

---

## 1. REST API Contracts

### 1.1. `POST /api/v1/meetings` (Tạo buổi sinh hoạt)
- **Mô tả**: Tạo buổi sinh hoạt mới, tự động ghi nhận người gửi request là người tạo (`created_by`).
- **Quyền hạn**: Người dùng có quyền `MeetingPermission.CREATE`.
- **Response**: `ApiResponse[MeetingResponse]` (Status 201 Created)
- **Response Schema (`MeetingResponse`)**:
  ```json
  {
    "code": 201,
    "message": "Meeting created successfully",
    "data": {
      "id": 105,
      "title": "Sinh hoạt chuyên đề AI",
      "content": "Nội dung buổi học",
      "start_time": "2026-10-24T18:00:00",
      "end_time": "2026-10-24T20:00:00",
      "require_check_in": true,
      "enable_evaluation": true,
      "evaluation_deadline": "2026-10-25T20:00:00",
      "created_by": 42,
      "trainer": {
        "id": 42,
        "name": "Nguyen Van A",
        "avatar_url": "https://..."
      },
      "created_at": "2026-10-24T10:00:00",
      "updated_at": "2026-10-24T10:00:00"
    }
  }
  ```

---

### 1.2. `GET /api/v1/meetings/{meeting_id}` (Chi tiết buổi sinh hoạt)
- **Mô tả**: Lấy thông tin chi tiết buổi sinh hoạt kèm danh sách thành viên tham gia.
- **Quyền hạn**: Người dùng đã đăng nhập có quyền `MeetingPermission.READ`.
- **Response**: `ApiResponse[MeetingDetailResponse]` (Status 200 OK)
- **Response Schema (`MeetingDetailResponse`)**:
  ```json
  {
    "code": 200,
    "message": "Meeting retrieved successfully",
    "data": {
      "id": 105,
      "title": "Sinh hoạt chuyên đề AI",
      "content": "Nội dung buổi học",
      "start_time": "2026-10-24T18:00:00",
      "end_time": "2026-10-24T20:00:00",
      "require_check_in": true,
      "enable_evaluation": true,
      "evaluation_deadline": "2026-10-25T20:00:00",
      "created_by": 42,
      "trainer": {
        "id": 42,
        "name": "Nguyen Van A",
        "avatar_url": "https://..."
      },
      "participants": [
        {
          "id": 201,
          "meeting_id": 105,
          "user_id": 55,
          "user_name": "Tran Van B",
          "user_avatar_url": null,
          "status": "JOINED",
          "check_in_at": "2026-10-24T18:05:00",
          "check_out_at": "2026-10-24T20:00:00",
          "link_image": null
        }
      ],
      "created_at": "2026-10-24T10:00:00",
      "updated_at": "2026-10-24T10:00:00"
    }
  }
  ```

---

### 1.3. `POST /api/v1/meetings/{meeting_id}/evaluations/overall` (Trainer đánh giá tổng thể buổi học)
- **Mô tả**: Gửi hoặc cập nhật phiếu đánh giá tổng thể cho buổi sinh hoạt.
- **Quyền hạn**: 
  - Quản trị viên (`admin`, `superadmin`, `leader`, `manager`) HOẶC
  - Người tạo cuộc họp (`meeting.created_by == current_user.id`) HOẶC
  - Trainer được phân công (`meeting.trainer.id == current_user.id`).
- **Request Body**:
  ```json
  {
    "scores": [
      { "criteria_code": "ORGANIZATION", "score": 5 },
      { "criteria_code": "TRAINEE_ENGAGEMENT", "score": 4 },
      { "criteria_code": "SCHEDULE_ADHERENCE", "score": 5 },
      { "criteria_code": "FACILITY_ENVIRONMENT", "score": 4 }
    ],
    "general_feedback": "Buổi sinh hoạt diễn ra sôi nổi, học viên tham gia tích cực."
  }
  ```
- **Responses**:
  - `201 Created`: Gửi đánh giá thành công. Trả về `MeetingOverallEvaluationResponse`.
  - `400 Bad Request`: Buổi học chưa bắt đầu, hoặc đã quá hạn 24h, hoặc điểm số không hợp lệ.
  - `403 Forbidden`: Người dùng không phải là người tạo, không phải Trainer, và không phải Quản trị viên.
  - `404 Not Found`: Không tìm thấy buổi sinh hoạt.

---

### 1.4. `POST /api/v1/meetings/{meeting_id}/evaluations/trainer` (Trainer đánh giá từng học viên)
- **Mô tả**: Trainer gửi hoặc cập nhật điểm đánh giá cho một học viên tham gia buổi học.
- **Quyền hạn**:
  - Quản trị viên (`admin`, `superadmin`, `leader`, `manager`) HOẶC
  - Người tạo cuộc họp (`meeting.created_by == current_user.id`) HOẶC
  - Trainer được phân công (`meeting.trainer.id == current_user.id`).
- **Request Body**:
  ```json
  {
    "target_user_id": 55,
    "scores": [
      { "criteria_code": "ATTENDANCE_CONDUCT", "score": 5 },
      { "criteria_code": "INTERACTION_CONTRIBUTION", "score": 4 },
      { "criteria_code": "ASSIGNMENT_QUALITY", "score": 4 },
      { "criteria_code": "TECHNICAL_UNDERSTANDING", "score": 5 }
    ],
    "feedback_text": "Tiếp thu tốt, trả lời câu hỏi xuất sắc."
  }
  ```
- **Responses**:
  - `201 Created`: Đánh giá học viên thành công. Trả về `EvaluationResponse`.
  - `400 Bad Request`: Học viên không có trong danh sách hoặc đã vắng mặt trong buổi học.
  - `403 Forbidden`: Người dùng không có quyền Trainer/Creator của buổi học này.
  - `404 Not Found`: Không tìm thấy buổi học.

---

## 2. Frontend Component & Contract Behaviors

### 2.1. Logic xác định vai trò Trainer trên Client
- Áp dụng trên cả Web Frontend và Zalo Mini App:
  ```typescript
  const isTrainer = Boolean(
    (meeting.created_by && Number(currentUserId) === Number(meeting.created_by)) ||
    (meeting.trainer?.id && Number(currentUserId) === Number(meeting.trainer.id)) ||
    (user?.role_names?.some((r) => ['admin', 'leader', 'superadmin', 'manager'].includes(r.toLowerCase())))
  );
  ```

### 2.2. Quy tắc hiển thị nút thao tác (UI Visibility Rules)

| Nút thao tác | Điều kiện hiển thị | Hành vi khi kích hoạt |
| :--- | :--- | :--- |
| **"Bật Đánh giá 2 chiều"** (Header) | `isTrainer && !meeting.enable_evaluation` | Gọi API cập nhật `{ enable_evaluation: true }` |
| **"Trainer đánh giá buổi học"** (Header) | `isTrainer && meeting.enable_evaluation && isEnded` | Mở `MeetingOverallEvaluationModal` |
| **"Đánh giá" / "Đã ĐG (X.X)"** (Bảng học viên) | `isTrainer && meeting.enable_evaluation` | Mở `TrainerEvaluationModal` tương ứng với học viên |
| **"Điểm của tôi"** (Header & Banner) | `isTrainee && meeting.enable_evaluation` | Mở `MyEvaluationResultModal` |
| **"Đánh giá Trainer"** (Header & Banner) | `isTrainee && meeting.enable_evaluation` | Mở `TraineeEvaluationModal` |
