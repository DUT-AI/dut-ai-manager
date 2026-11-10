# Phase 1: Data Model & Contracts - Require Current Meeting for Change

## 1. Domain Payload Schema (`ChangeMeetingPayload`)

Cập nhật tại `backend/app/permission_request/domain/payloads.py`:

```python
class ChangeMeetingPayload(BasePermissionPayload):
    """Payload cho đơn xin đổi buổi sinh hoạt (CHANGE_MEETING)."""

    category: Literal[RequestCategory.CHANGE_MEETING] = RequestCategory.CHANGE_MEETING
    meeting_id: int  # Buổi đích chuyển đến (bắt buộc)
    old_meeting_id: int  # Buổi hiện tại chuyển đi (bắt buộc, không được None)
    start_time: datetime | None = None
```

## 2. API Error Contracts

Khi validate thất bại trong `ChangeMeetingStrategy.validate(...)`:
- **Thiếu `old_meeting_id`**: HTTP 400 / 422: `"Vui lòng chọn buổi sinh hoạt hiện tại"`
- **Không tìm thấy ca hiện tại**: HTTP 404: `"Không tìm thấy buổi sinh hoạt hiện tại đã chọn"`
- **User không có mặt trong ca hiện tại**: HTTP 400: `"Bạn không có mặt trong danh sách tham gia của buổi sinh hoạt hiện tại đã chọn"`
- **Ca hiện tại và ca đích trùng nhau**: HTTP 400: `"Không thể đổi sang cùng một buổi họp"`
- **Ca đích đã bắt đầu / trong quá khứ**: HTTP 400: `"Không thể đổi sang buổi họp đã bắt đầu hoặc đã kết thúc"`
- **Ca đích hết chỗ ngồi**: HTTP 400: `"Buổi họp đích đã hết chỗ ngồi (0/30)"`

## 3. Frontend Form Contracts

- Web: `PermissionFormModal.tsx`
  - Field `old_meeting_id`: Bắt buộc, kiểu `number`.
  - Field `meeting_id`: Bắt buộc, kiểu `number`.
- Zalo Mini App: `PermissionFormModal.tsx`
  - `formOldMeetingId`: Bắt buộc.
  - `formMeetingId`: Bắt buộc.
