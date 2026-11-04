# Implementation Plan: Đồng Bộ Điều Phối Tác Vụ Nền Trong Môi Trường Đa Tiến Trình (Multi-Worker Scheduler Synchronization)

**Branch**: `050-multi-worker-scheduler-lock` | **Date**: 2026-11-05 | **Spec**: [specs/050-multi-worker-scheduler-lock/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/spec.md)

**Input**: Feature specification from `specs/050-multi-worker-scheduler-lock/spec.md` (Đã tinh gọn: loại bỏ ENABLE_SCHEDULER)

---

## Summary

Triển khai cơ chế **Bầu chọn Thủ lĩnh Tự Động (Zero-Config Leader Election)** sử dụng **Redis Distributed Lock** cho hệ thống lập lịch tác vụ nền (`APScheduler`), cho phép máy chủ ứng dụng FastAPI nâng số lượng worker (`uvicorn --workers 4`) trong container Docker lên nhiều tiến trình đồng thời để tăng năng lực xử lý Web API, trong khi vẫn đảm bảo tuyệt đối chỉ có duy nhất MỘT tiến trình đảm nhận việc quét và chạy các tác vụ định kỳ (không nhân bản thông báo và tránh xung đột dữ liệu). Mọi worker khi khởi chạy đều tự động kết nối Redis tranh chấp quyền, không đòi hỏi bất kỳ biến cấu hình bật/tắt thủ công nào. Hệ thống hỗ trợ tự động chuyển giao quyền (Failover) khi tiến trình Leader gặp sự cố.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**:
- `fastapi>=0.128.0`
- `uvicorn[standard]>=0.40.0`
- `apscheduler>=3.11.2`
- `redis>=5.0.0` (Thư viện Redis async chính thức `redis.asyncio`)
- `dishka>=1.9.1` (IoC / Dependency Injection)
- `pydantic-settings>=2.12.0`  
**Storage**:
- PostgreSQL 16 (Dữ liệu quan hệ nghiệp vụ chính)
- Redis 7 (`redis:7-alpine`, In-memory Distributed Lock & Coordinator)  
**Testing**: `pytest>=8.0.0`, `pytest-asyncio`, `pytest-mock`  
**Target Platform**: Linux Container (Docker / Docker Compose), macOS/Linux local dev  
**Project Type**: Web Service (FastAPI REST Backend + Background Worker)  
**Performance Goals**:
- Chiếm khóa và gia hạn heartbeat qua Redis có độ trễ <2ms.
- 0% nhân bản tác vụ nền trên toàn bộ các chu kỳ thực thi.
- Thời gian tự động chuyển giao quyền Leader khi có sự cố <40 giây (thỏa mãn tiêu chí <60 giây).  
**Constraints**:
- Khi Redis tạm thời mất kết nối, hệ thống Web API vẫn tiếp tục phục vụ người dùng bình thường, không gây crash tiến trình.
- Không thay đổi mã nguồn các job nghiệp vụ hiện có (`app/jobs/*`).
- Giải phóng khóa an toàn bằng Lua script để chống race condition.  
**Scale/Scope**: Hỗ trợ mở rộng từ 1 đến 16 workers trên mỗi máy chủ hoặc nhiều containers chạy song song.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên Tắc Hiến Pháp | Đánh Giá Tính Tuân Thủ | Trạng Thái |
| :--- | :--- | :--- |
| **I. Clean Architecture & DDD Boundaries** | Module điều phối Scheduler và Redis Client được đặt tại tầng Hạ tầng/Hạt nhân (`app.core` & `app.shared.infrastructure`). Nghiệp vụ job và domain không bị phụ thuộc vào Redis. | **PASS** |
| **II. Dependency Injection with Dishka** | Đăng ký `redis.asyncio.Redis` và connection pool tập trung vào `InfrastructureProvider` (`app/shared/providers.py`) với `Scope.APP`. | **PASS** |
| **III. Enterprise UTC & Vietnam Display** | Toàn bộ CronTrigger của APScheduler giữ nguyên múi giờ chuẩn `Asia/Ho_Chi_Minh` cho các mốc thời gian Việt Nam (23:59, 00:01). | **PASS** |
| **IV. Event-Driven Decoupling** | Các job nền tiếp tục bắn domain event qua `EventBus`, không ảnh hưởng tới kiến trúc event-driven. | **PASS** |
| **V. API Backward Compatibility** | Không thay đổi bất kỳ REST API endpoint nào của hệ thống. | **PASS** |
| **VII. Single-Responsibility Use Cases** | Không tạo use case thừa; tác vụ nền được điều phối qua một Coordinator chuyên trách (`SchedulerCoordinator`). | **PASS** |
| **IX. Pure Composition Over Base Use Cases** | `SchedulerCoordinator` được thiết kế theo dạng Composition độc lập, không dùng kế thừa. | **PASS** |
| **XIV. No Fake Optionals & Fail-Fast Contracts** | Các tham số khởi tạo Coordinator (`redis_client`, `dishka_container`, `worker_id`) là các tham số bắt buộc, không sử dụng default `None` lỏng lẻo. | **PASS** |
| **XV. Unified Client Networking & Session Security** | Giữ nguyên và bảo vệ toàn vẹn các chuẩn mực xác thực vừa hoàn thành trong feature 049. | **PASS** |

**Kết luận Gate**: Toàn bộ 9 tiêu chí đánh giá đều **PASS**. Không có vi phạm kiến trúc nào.

---

## Project Structure

### Documentation (this feature)

```text
specs/050-multi-worker-scheduler-lock/
├── spec.md              # Đặc tả yêu cầu người dùng và tiêu chí thành công
├── plan.md              # Kế hoạch triển khai (File hiện tại)
├── research.md          # Nghiên cứu kỹ thuật, phân tích phương án và quyết định
├── data-model.md        # Mô hình dữ liệu thực thể, trạng thái và schema Redis
├── quickstart.md        # Hướng dẫn kiểm thử và xác minh tính năng
├── contracts/           # Các đặc tả hợp đồng kỹ thuật
│   ├── redis-lock-contract.md          # Đặc tả lệnh Redis, TTL, Lua script nguyên tử
│   └── environment-config-contract.md  # Cấu hình biến môi trường Redis và Docker
└── checklists/
    └── requirements.md  # Đánh giá độ phủ yêu cầu (16/16 Pass)
```

### Source Code Layout (backend)

```text
backend/
├── pyproject.toml                         # Bổ sung dependency "redis>=5.0.0"
├── Dockerfile                             # Cập nhật CMD chạy uvicorn với workers linh hoạt
├── app/
│   ├── core/
│   │   ├── config.py                      # Thêm REDIS_HOST, REDIS_PORT, UVICORN_WORKERS...
│   │   ├── scheduler.py                   # Tái cấu trúc: hàm start/shutdown scheduler
│   │   ├── scheduler_types.py             # Định nghĩa LeaderRole, WorkerIdentity, State
│   │   └── scheduler_coordinator.py       # Bộ điều phối Leader Election qua Redis
│   ├── shared/
│   │   ├── infrastructure/
│   │   │   └── redis_client.py            # Quản lý kết nối Async Redis Client
│   │   └── providers.py                   # Cung cấp Redis Client trong InfrastructureProvider
│   └── main.py                            # Tích hợp Coordinator vào lifespan startup & shutdown
└── tests/
    └── unit/
        └── test_scheduler_coordinator.py  # Bộ unit test cho Leader Election & Failover

docker-compose.yml                         # Bổ sung service redis:7-alpine và network liên kết
```

---

## Complexity Tracking

> Không có vi phạm kiến trúc nào cần biện minh (Zero violations detected).
