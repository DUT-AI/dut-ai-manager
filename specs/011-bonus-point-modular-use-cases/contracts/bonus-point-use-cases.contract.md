# Hợp đồng Giao tiếp: Tầng Ứng dụng Điểm Thưởng (Contract)

**Feature**: `011-bonus-point-modular-use-cases`
**Date**: 2026-10-17

## 1. Giao thức Xuất nhập khẩu (Export Interface Contract)

### 1.1 `app.bonus_point.application.__init__.py`
Tệp khởi tạo gói PHẢI xuất khẩu các use cases qua danh sách `__all__`:

```python
__all__ = [
    "GetBonusPointsUseCase",
    "CreateBonusPointsUseCase",
    "UpdateBonusPointUseCase",
    "DeleteBonusPointUseCase",
    "RestoreBonusPointUseCase",
    "CalculateActivityPointsUseCase",
]
```

---

## 2. Hợp đồng Phương thức của Từng Use Case

### 2.1 `GetBonusPointsUseCase.execute`
- **Tham số**:
  - `user_id: int | None = None`
  - `type: BonusPointType | None = None`
  - `month: int | None = None`
  - `year: int | None = None`
  - `start_date: date | None = None`
  - `end_date: date | None = None`
  - `page: int = 1`
  - `page_size: int = 20`
  - `deleted: bool = False`
- **Kết quả trả về**: `tuple[list[BonusPoint], int]` (Danh sách thực thể và tổng số lượng bản ghi).

### 2.2 `CreateBonusPointsUseCase.execute`
- **Tham số**:
  - `data: BonusPointCreate`
  - `current_user_name: str | None = None`
- **Kết quả trả về**: `list[BonusPoint]` (Danh sách thực thể đã được lưu).
- **Side-effects**: Phát hành sự kiện `BonusPointCreated` cho từng bản ghi.

### 2.3 `UpdateBonusPointUseCase.execute`
- **Tham số**:
  - `entity_id: int`
  - `data: BonusPointUpdate`
  - `current_user_name: str | None = None`
- **Kết quả trả về**: `BonusPoint | None`.
- **Side-effects**: Phát hành sự kiện `BonusPointUpdated`.

### 2.4 `DeleteBonusPointUseCase.execute`
- **Tham số**: `entity_id: int`
- **Kết quả trả về**: `bool` (Thành công hay không).
- **Side-effects**: Phát hành sự kiện `BonusPointDeleted`.

### 2.5 `RestoreBonusPointUseCase.execute`
- **Tham số**: `entity_id: int`
- **Kết quả trả về**: `BonusPoint | None`.

### 2.6 `CalculateActivityPointsUseCase.execute`
- **Tham số**: `since: datetime | None = None`
- **Kết quả trả về**: `int` (Số lượng bản ghi điểm thưởng đã được tạo tự động).
