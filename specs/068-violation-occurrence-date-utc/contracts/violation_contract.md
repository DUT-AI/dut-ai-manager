# Contracts: Violation API Schema & Event Payload

## 1. REST API Contract: Violation Response DTO

### Endpoint
`GET /api/v1/violations`

### Response Payload Schema (`ViolationResponse`)
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 105,
        "user_id": 42,
        "reason": "Vắng sinh hoạt: Buổi hướng dẫn đồ án (Không xin phép)",
        "date": "2026-11-10T11:00:00Z",
        "created_at": "2026-11-12T16:59:00Z",
        "updated_at": "2026-11-12T16:59:00Z",
        "owner": {
          "id": 42,
          "name": "Nguyễn Văn A",
          "avatar_url": "https://..."
        },
        "creator": null
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

**Lưu ý quan trọng**:
- Trường `date` trả về chuẩn ISO 8601 kèm ký tự `Z` hoặc `+00:00`.
- Client hiển thị thời gian bằng:
  ```typescript
  dayjs(record.date).format('DD/MM/YYYY HH:mm')
  ```
  Với `date = "2026-11-10T11:00:00Z"`, client ở múi giờ UTC+7 (Việt Nam) sẽ hiển thị thành `10/11/2026 18:00`.
  Trường `created_at = "2026-11-12T16:59:00Z"` thể hiện thời điểm job quét và tạo bản ghi (23:59:00 UTC+7 ngày 12/11). Hai mốc thời gian này được phân tách rõ ràng.
