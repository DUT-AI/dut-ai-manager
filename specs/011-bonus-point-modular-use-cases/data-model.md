# Mô hình Cấu trúc & Thực thể: Miền Điểm Thưởng (Data Model)

**Feature**: `011-bonus-point-modular-use-cases`
**Date**: 2026-10-17

## 1. Sơ đồ Cấu trúc Tầng Ứng dụng (Application Layer Structure)

```
backend/app/bonus_point/application/
├── __init__.py                               # Re-export tất cả qua __all__ (Constitution VII)
├── dtos.py                                   # BonusPointCreate, BonusPointUpdate, BonusPointResponse
├── get_bonus_points_use_case.py              # GetBonusPointsUseCase
├── create_bonus_points_use_case.py           # CreateBonusPointsUseCase
├── update_bonus_point_use_case.py            # UpdateBonusPointUseCase
├── delete_bonus_point_use_case.py            # DeleteBonusPointUseCase
├── restore_bonus_point_use_case.py           # RestoreBonusPointUseCase
└── calculate_activity_points_use_case.py     # CalculateActivityPointsUseCase
```

---

## 2. Chi tiết Phụ thuộc của Từng Use Case

| Tệp Use Case | Lớp Use Case | Phụ thuộc Injection (Dependencies) | Sự kiện Miền Phát ra (Events) |
| :--- | :--- | :--- | :--- |
| `get_bonus_points_use_case.py` | `GetBonusPointsUseCase` | `BonusPointRepository` | Không |
| `create_bonus_points_use_case.py` | `CreateBonusPointsUseCase` | `BonusPointRepository`, `EventBus` | `BonusPointCreated` |
| `update_bonus_point_use_case.py` | `UpdateBonusPointUseCase` | `BonusPointRepository`, `EventBus` | `BonusPointUpdated` |
| `delete_bonus_point_use_case.py` | `DeleteBonusPointUseCase` | `BonusPointRepository`, `EventBus` | `BonusPointDeleted` |
| `restore_bonus_point_use_case.py` | `RestoreBonusPointUseCase` | `BonusPointRepository` | Không |
| `calculate_activity_points_use_case.py` | `CalculateActivityPointsUseCase` | `ParticipantRepository`, `BonusPointRepository` | Không (Lưu trực tiếp qua repo) |

---

## 3. Các Thực thể & Đối tượng Giá trị Liên quan

- **`BonusPoint`** (`app.bonus_point.domain.entity`): Thực thể lưu trữ thông tin điểm thưởng (`points`, `reason`, `date`, `type`, `user_id`).
- **`BonusPointType`** (`app.bonus_point.domain.value_objects`): Enum gồm các loại `CLUB_ACTIVITY`, `CONTRIBUTION`, `OTHER`.
- **`BonusPointCreate` / `BonusPointUpdate`** (`app.bonus_point.application.dtos`): DTOs cho các thao tác ghi dữ liệu.
