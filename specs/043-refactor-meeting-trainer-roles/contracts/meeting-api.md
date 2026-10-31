# Contracts: Meeting Management API with Trainer & Trainee Roles

**Feature**: `043-refactor-meeting-trainer-roles`  
**Date**: 2026-11-01  

---

## 1. Create Meeting (`POST /api/v1/meetings`)

### Request Body:
```json
{
  "title": "Machine Learning Lab 1",
  "content": "Giới thiệu Scikit-Learn và Decision Tree",
  "start_time": "2026-11-05T19:00:00+07:00",
  "end_time": "2026-11-05T21:00:00+07:00",
  "require_check_in": true,
  "enable_evaluation": true,
  "trainer_ids": [10],
  "trainee_ids": [21, 22, 23]
}
```

### Response (200 OK):
```json
{
  "is_success": true,
  "code": 200,
  "data": {
    "id": 105,
    "title": "Machine Learning Lab 1",
    "created_by": 1,
    "trainer": {
      "id": 10,
      "name": "Nguyễn Văn Mentor",
      "avatar_url": "https://..."
    },
    "trainers": [
      {
        "id": 10,
        "name": "Nguyễn Văn Mentor",
        "avatar_url": "https://..."
      }
    ],
    "participants": [
      {
        "id": 1001,
        "meeting_id": 105,
        "user_id": 10,
        "role": "TRAINER",
        "status": "NOT_JOINED",
        "user_name": "Nguyễn Văn Mentor"
      },
      {
        "id": 1002,
        "meeting_id": 105,
        "user_id": 21,
        "role": "TRAINEE",
        "status": "NOT_JOINED",
        "user_name": "Trần Văn Học Viên"
      }
    ]
  }
}
```

---

## 2. Update Meeting (`PUT /api/v1/meetings/{id}`)

### Request Body:
```json
{
  "trainer_ids": [10, 11],
  "trainee_ids": [21, 22, 23, 24]
}
```

---

## 3. Quyền Hạn (Authorization)

| Thao tác | Admin / Leader | Người tạo (`created_by`) | Trainer (`role == TRAINER`) | Trainee (`role == TRAINEE`) |
| :--- | :---: | :---: | :---: | :---: |
| Xem danh sách / Chi tiết buổi học | ✅ | ✅ | ✅ | ✅ |
| Chỉnh sửa thông tin buổi học | ✅ | ✅ | ✅ | ❌ |
| Điểm danh / Sửa trạng thái học viên | ✅ | ✅ | ✅ | ❌ |
| Nộp Đánh giá tổng thể buổi học | ✅ | ✅ | ✅ | ❌ |
| Đánh giá từng Trainee (`TRAINER_TO_TRAINEE`) | ✅ | ✅ | ✅ | ❌ |
| Đánh giá Trainer (`TRAINEE_TO_TRAINER`) | ❌ | ❌ | ❌ | ✅ |
| Nhận thông báo nhắc nhở nộp đánh giá | - | - | ✅ (Nhắc nộp đánh giá tổng thể & Trainees) | ✅ (Nhắc đánh giá Trainer) |
