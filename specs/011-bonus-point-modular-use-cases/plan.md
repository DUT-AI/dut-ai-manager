# Implementation Plan: Tách Biệt Use Cases Đơn Nhiệm Miền Điểm Thưởng (Bonus Point Modular Use Cases)

**Branch**: `011-bonus-point-modular-use-cases` | **Date**: 2026-10-17 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/011-bonus-point-modular-use-cases/spec.md)

**Input**: Đặc tả tính năng từ `/specs/011-bonus-point-modular-use-cases/spec.md` theo yêu cầu refactor tách tệp `use_cases.py` thành các tệp riêng lẻ như module `meeting` và xóa bỏ hoàn toàn tệp `use_cases.py`.

---

## 1. Summary

Thực hiện chia tách tệp nguyên khối `backend/app/bonus_point/application/use_cases.py` (chứa 6 use cases) thành 6 tệp đơn nhiệm riêng biệt tuân thủ tuyệt đối Điều lệ Dự án (**Constitution Principle VII: Single-Responsibility Use Cases**). Tệp nguyên khối `use_cases.py` sẽ bị xóa bỏ hoàn toàn không giữ file shim tương thích ngược theo chỉ thị người dùng. Tất cả 6 use case sẽ được re-export minh bạch qua `backend/app/bonus_point/application/__init__.py` thông qua biến `__all__`. Đồng thời, chuẩn hóa các câu lệnh import tại tất cả 3 vị trí phụ thuộc (`providers.py`, `controller.py`, `app/jobs/activity_scoring_job.py`) sang import trực tiếp từ `app.bonus_point.application`.

---

## 2. Technical Context

- **Language/Version**: Python 3.12 (môi trường ảo `backend/.venv`)
- **Primary Dependencies**: FastAPI, Dishka (Dependency Injection), SQLAlchemy 2.0, Pydantic V2
- **Storage**: PostgreSQL (SQLAlchemy ORM với `BonusPointModel`)
- **Testing**: PyTest (`pytest backend/tests/api/test_bonus_point_api.py`, `pytest backend/tests/unit/test_billing_use_cases.py`)
- **Target Platform**: Linux Server / Docker Backend Service
- **Project Type**: Web Service API (Backend Clean Architecture)
- **Performance Goals**: Zero latency overhead (việc tách module cấp độ tệp tin chỉ ảnh hưởng tĩnh tại thời điểm nạp module)
- **Constraints**: 
  - Không thay đổi logic nghiệp vụ tính điểm hoặc phát sự kiện miền (`EventBus.publish`).
  - Xóa bỏ triệt để `use_cases.py`, không để lại dead code hoặc circular imports.
- **Scale/Scope**: 6 use case classes, 1 `__init__.py`, 3 call sites, 0 test regressions.

---

## 3. Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái | Ghi chú |
| :--- | :--- | :---: | :--- |
| **Principle I: Clean Architecture & Practical DDD** | Application layer chỉ điều phối logic miền, repository và phát domain event. | **PASS** | Bảo toàn ranh giới giữa Domain, Application và Infrastructure. |
| **Principle II: Dependency Injection with Dishka** | Tất cả use cases được đăng ký qua `providers.py` và giải quyết qua container. | **PASS** | Tên lớp và method signature giữ nguyên 100%, Dishka resolve hoàn toàn tương thích. |
| **Principle III: Unified UTC+7 Timezone** | Thời gian và ngày tháng giữ nguyên múi giờ UTC+7. | **PASS** | Không can thiệp vào logic tính toán thời gian. |
| **Principle IV: Event-Driven Decoupling** | Giữ nguyên việc publish các domain event `BonusPointCreated`, `BonusPointUpdated`, `BonusPointDeleted`. | **PASS** | Sự kiện được xuất bản bất đồng bộ qua `EventBus` như thiết kế cũ. |
| **Principle V: API Backward Compatibility** | Giữ nguyên API contract và Response models. | **PASS** | Không ảnh hưởng đến các router HTTP hay schema JSON. |
| **Principle VII: Single-Responsibility Use Cases** | Mỗi use case PHẢI nằm trong 1 tệp `*_use_case.py` riêng biệt; `__init__.py` xuất khẩu qua `__all__`; cấm gom vào `use_cases.py`. | **PASS** | Đây chính là mục tiêu tiên quyết của kế hoạch này. |

---

## 4. Project Structure

### Documentation (this feature)

```text
specs/011-bonus-point-modular-use-cases/
├── plan.md              # Kế hoạch triển khai kiến trúc (tệp này)
├── research.md          # Kết quả khảo sát mã nguồn & phương án refactor
├── data-model.md        # Cấu trúc tệp thư mục & phân loại phụ thuộc use cases
├── quickstart.md        # Hướng dẫn kiểm thử tự động & xác nhận xóa file
├── contracts/
│   └── bonus-point-use-cases.contract.md # Hợp đồng giao tiếp & chữ ký phương thức
└── checklists/
    └── requirements.md  # Danh sách kiểm tra chất lượng đặc tả
```

### Source Code Layout

```text
backend/app/
├── bonus_point/
│   ├── application/
│   │   ├── __init__.py                               # Re-export cả 6 use case qua __all__
│   │   ├── dtos.py                                   # Giữ nguyên
│   │   ├── get_bonus_points_use_case.py              # [MỚI] Tách GetBonusPointsUseCase
│   │   ├── create_bonus_points_use_case.py           # [MỚI] Tách CreateBonusPointsUseCase
│   │   ├── update_bonus_point_use_case.py            # [MỚI] Tách UpdateBonusPointUseCase
│   │   ├── delete_bonus_point_use_case.py            # [MỚI] Tách DeleteBonusPointUseCase
│   │   ├── restore_bonus_point_use_case.py           # [MỚI] Tách RestoreBonusPointUseCase
│   │   ├── calculate_activity_points_use_case.py     # [MỚI] Tách CalculateActivityPointsUseCase
│   │   └── use_cases.py                              # [XÓA BỎ HOÀN TOÀN]
│   ├── controller.py                                 # Cập nhật import từ app.bonus_point.application
│   └── providers.py                                  # Cập nhật import từ app.bonus_point.application
└── jobs/
    └── activity_scoring_job.py                       # Cập nhật import từ app.bonus_point.application
```

---

## 5. Implementation Phases

### Phase 1: Chuẩn bị & Trích xuất các Use Case Đơn Nhiệm
1. Tạo 6 tệp mới trong thư mục `backend/app/bonus_point/application/`:
   - `get_bonus_points_use_case.py`
   - `create_bonus_points_use_case.py`
   - `update_bonus_point_use_case.py`
   - `delete_bonus_point_use_case.py`
   - `restore_bonus_point_use_case.py`
   - `calculate_activity_points_use_case.py`
2. Đưa đúng các imports cần thiết vào từng file (Repository, EventBus, Entities, DTOs).

### Phase 2: Cấu hình Re-export tại `__init__.py`
1. Cập nhật `backend/app/bonus_point/application/__init__.py`:
   - Import cả 6 lớp use case từ các module con tương ứng.
   - Định nghĩa `__all__` chứa đầy đủ 6 tên lớp.

### Phase 3: Chuẩn hóa Điểm Gọi (Call Sites) & Xóa Bỏ File Cũ
1. Cập nhật import trong `backend/app/bonus_point/providers.py` -> `from app.bonus_point.application import (...)`.
2. Cập nhật import trong `backend/app/bonus_point/controller.py` -> `from app.bonus_point.application import (...)`.
3. Cập nhật import trong `backend/app/jobs/activity_scoring_job.py` -> `from app.bonus_point.application import CalculateActivityPointsUseCase`.
4. Xóa vĩnh viễn tệp `backend/app/bonus_point/application/use_cases.py`.

### Phase 4: Kiểm thử Xác minh & Đảm bảo Zero Regression
1. Kiểm tra tĩnh: Xác nhận không còn chuỗi `app.bonus_point.application.use_cases` trong toàn bộ repo (`grep_search`).
2. Chạy kiểm thử pytest:
   - `backend/.venv/bin/pytest backend/tests/api/test_bonus_point_api.py -v`
   - `backend/.venv/bin/pytest backend/tests/unit/test_billing_use_cases.py -v`
   - `backend/.venv/bin/pytest backend/tests/api/test_report_api.py -v`

---

## 6. Complexity Tracking

> Không có vi phạm Constitution nào cần biện minh. Toàn bộ thiết kế đưa codebase về đúng chuẩn Constitution Principle VII.
