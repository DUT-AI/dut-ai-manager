# Meeting Sub-Modules API Contract Documentation

**Base Prefix**: `/api/v1/meetings`  
**Authentication**: Bearer JWT / Cookie / Role API Key  
**Tags**: `meetings`

---

## 1. Sub-Router: Meeting Lifecycle (`meeting_controller.py`)

| Method | Relative Path | Full Path | Description | Access |
|---|---|---|---|---|
| `POST` | `/` | `/api/v1/meetings/` | Create a new meeting | Admin / Leader |
| `GET` | `/` | `/api/v1/meetings/` | List meetings with filters & pagination | Authenticated |
| `GET` | `/upcoming-with-seats` | `/api/v1/meetings/upcoming-with-seats` | List upcoming meetings with remaining seats | Authenticated |
| `GET` | `/{meeting_id}` | `/api/v1/meetings/{meeting_id}` | Get meeting details by ID | Authenticated |
| `PUT` | `/{meeting_id}` | `/api/v1/meetings/{meeting_id}` | Update meeting details | Creator / Admin |
| `DELETE` | `/{meeting_id}` | `/api/v1/meetings/{meeting_id}` | Soft delete meeting | Creator / Admin |

---

## 2. Sub-Router: Attendance & Check-in (`attendance_controller.py`)

| Method | Relative Path | Full Path | Description | Access |
|---|---|---|---|---|
| `POST` | `/check-in-with-card` | `/api/v1/meetings/check-in-with-card` | ESP32 / RFID Card Check-in (Audio feedback) | Public / API Key |
| `POST` | `/check-in` | `/api/v1/meetings/check-in` | Self check-in with optional selfie upload | Authenticated |
| `POST` | `/checkout` | `/api/v1/meetings/checkout` | Self check-out | Authenticated |
| `PUT` | `/{meeting_id}/participants/{user_id}/status` | `/api/v1/meetings/{meeting_id}/participants/{user_id}/status` | Manual attendance status update (Option A) | Creator / Admin / Trainer |
| `POST` | `/{meeting_id}/batch-check-in` | `/api/v1/meetings/{meeting_id}/batch-check-in` | Batch quick check-in for all attendees | Creator / Admin / Trainer |

---

## 3. Sub-Router: Evaluations (`evaluation_controller.py`)

| Method | Relative Path | Full Path | Description | Access |
|---|---|---|---|---|
| `POST` | `/{meeting_id}/trainer-evaluations` | `/api/v1/meetings/{meeting_id}/trainer-evaluations` | Trainer submits evaluation for a trainee | Trainer / Creator |
| `POST` | `/{meeting_id}/trainee-evaluations` | `/api/v1/meetings/{meeting_id}/trainee-evaluations` | Trainee submits evaluation for the trainer | Trainee |
| `POST` | `/{meeting_id}/overall-evaluation` | `/api/v1/meetings/{meeting_id}/overall-evaluation` | Trainer submits overall meeting evaluation | Trainer / Creator |
| `GET` | `/{meeting_id}/evaluations` | `/api/v1/meetings/{meeting_id}/evaluations` | Get all evaluations for a meeting | Creator / Admin |
| `GET` | `/{meeting_id}/evaluations/summary` | `/api/v1/meetings/{meeting_id}/evaluations/summary` | Get evaluation progress & statistics | Authenticated |
| `GET` | `/{meeting_id}/evaluations/my` | `/api/v1/meetings/{meeting_id}/evaluations/my` | Get current user's evaluation feedback | Authenticated |

---

## Contract Integrity Guarantee
All endpoint signatures, query parameters (`skip`, `limit`, `category`, `status`, `start_date`, `end_date`), headers (`X-Message`, `X-Audio-Length`), and response bodies remain 100% byte-for-byte compatible with existing frontend clients and automated hardware.
