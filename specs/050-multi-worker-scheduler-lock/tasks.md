---
description: "Task list for multi-worker scheduler synchronization feature implementation"
---

# Tasks: Đồng Bộ Điều Phối Tác Vụ Nền Trong Môi Trường Đa Tiến Trình (Multi-Worker Scheduler Synchronization)

**Input**: Design documents from `/specs/050-multi-worker-scheduler-lock/`  
**Prerequisites**: [plan.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/plan.md), [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/spec.md), [research.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/research.md), [data-model.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/data-model.md), [contracts/](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/050-multi-worker-scheduler-lock/contracts/)

## Format: `[ID] [P?] [Story] Description with file path`
- **[P]**: Có thể thực hiện song song (khác tệp, không phụ thuộc vào task chưa hoàn thành)
- **[Story]**: Gán nhãn User Story tương ứng (`[US1]`, `[US2]`)

---

## Phase 1: Setup (Hạ Tầng Dùng Chung)

**Mục đích**: Cài đặt thư viện Redis, cấu hình môi trường và dịch vụ docker-compose

- [X] T001 Cài đặt dependency `redis>=5.0.0` vào `backend/pyproject.toml` và đồng bộ môi trường với `uv sync`
- [X] T002 [P] Bổ sung dịch vụ `redis:7-alpine` kèm healthcheck và volume vào `docker-compose.yml`
- [X] T003 [P] Cập nhật lớp `Settings` trong `backend/app/core/config.py` để bổ sung các cấu hình kết nối Redis `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`, `UVICORN_WORKERS` và thuộc tính `REDIS_URL`

---

## Phase 2: Foundational (Các Điều Kiện Tiên Quyết)

**Mục đích**: Xây dựng kết nối Redis Client và các kiểu dữ liệu trạng thái điều phối làm nền tảng cho mọi User Story

**⚠️ QUAN TRỌNG**: Không bắt đầu triển khai các User Story trước khi Phase 2 hoàn tất

- [X] T004 Xây dựng module kết nối async Redis client trong `backend/app/shared/infrastructure/redis_client.py`
- [X] T005 Đăng ký `redis.asyncio.Redis` và connection pool vào Dishka `InfrastructureProvider` trong `backend/app/shared/providers.py` ở `Scope.APP`
- [X] T006 [P] Định nghĩa các kiểu dữ liệu trạng thái điều phối (`LeaderRole`, `WorkerIdentity`, `SchedulerCoordinatorState`) trong `backend/app/core/scheduler_types.py`

**Checkpoint**: Hạ tầng kết nối Redis và kiểu dữ liệu điều phối đã sẵn sàng. Có thể bắt đầu triển khai User Story 1.

---

## Phase 3: User Story 1 - Khởi Chạy Đa Worker Chỉ Duy Nhất 1 Leader Chạy APScheduler (Priority: P1) 🎯 MVP

**Mục tiêu**: Khi chạy nhiều worker uvicorn đồng thời, chỉ có duy nhất 1 worker giành được khóa `dut_ai:scheduler:leader_lock` và kích hoạt `APScheduler`, các worker còn lại ở chế độ Standby chỉ phục vụ API.

**Independent Test**: Khởi chạy 2+ workers uvicorn. Kiểm tra log chỉ có 1 worker báo đã giành quyền Leader và khởi động scheduler, các worker khác báo Standby. Kiểm tra trên Redis key `dut_ai:scheduler:leader_lock` tồn tại với TTL 30s.

### Tests cho User Story 1 ⚠️
- [X] T007 [P] [US1] Viết unit tests cho cơ chế tranh chấp khóa Leader (`acquire_leadership`, safe release bằng Lua script) trong `backend/tests/unit/test_scheduler_coordinator.py`

### Implementation cho User Story 1
- [X] T008 [US1] Hiện thực lớp `RedisSchedulerCoordinator` với phương thức `acquire_leadership()`, `release_leadership()` và cơ chế sinh `worker_id` duy nhất trong `backend/app/core/scheduler_coordinator.py`
- [X] T009 [US1] Tái cấu trúc `backend/app/core/scheduler.py` để bổ sung cấu hình job defaults (`max_instances=1`, `coalesce=True`, `misfire_grace_time=300`) và chuyển đổi sang hàm bất đồng bộ `async def start_scheduler(...)` / `async def shutdown_scheduler(...)`
- [X] T010 [US1] Tích hợp `RedisSchedulerCoordinator` vào lifecycle `lifespan` trong `backend/app/main.py` để tự động điều phối khởi động và tắt an toàn

**Checkpoint**: Đã hoàn thành User Story 1 (MVP). Hệ thống chạy được đa worker mà không bị trùng lặp scheduler.

---

## Phase 4: User Story 2 - Tự Động Failover & Heartbeat Khi Leader Gặp Sự Cố (Priority: P2)

**Mục tiêu**: Leader định kỳ gửi heartbeat 10s để duy trì TTL 30s. Nếu Leader bị dừng hoặc crash đột ngột, một trong các Standby worker sẽ tự động phát hiện và tiếp quản quyền Leader trong <40s.

**Independent Test**: Khởi chạy cụm worker. Xác định PID của Leader worker và kill tiến trình (`kill -9 <PID>`). Kiểm tra sau khi hết TTL, một worker Standby còn lại tự động giành khóa và kích hoạt scheduler.

### Tests cho User Story 2 ⚠️
- [X] T011 [P] [US2] Viết unit tests cho vòng lặp Heartbeat, mất quyền điều phối (Lost Leadership), và Standby polling tranh chấp lại khóa trong `backend/tests/unit/test_scheduler_coordinator.py`

### Implementation cho User Story 2
- [X] T012 [US2] Hiện thực background task `heartbeat_loop()` (mỗi 10s gia hạn TTL 30s qua Lua script) trong `backend/app/core/scheduler_coordinator.py`
- [X] T013 [US2] Hiện thực background task `standby_poll_loop()` (mỗi 10s thử giành lại khóa qua `SET NX EX 30`) trong `backend/app/core/scheduler_coordinator.py` để tự động khởi động scheduler khi trúng cử Leader
- [X] T014 [US2] Bổ sung xử lý lỗi gián đoạn kết nối Redis (Graceful Degradation: ghi log warning, thử lại với backoff, không làm gián đoạn tiến trình phục vụ Web API) trong `backend/app/core/scheduler_coordinator.py`

**Checkpoint**: Đã hoàn thành User Story 2. Hệ thống đạt độ tin cậy cao (High Availability), tự phục hồi khi có sự cố.

---

## Phase 5: Container Packaging & Multi-Worker Deployment

**Mục tiêu**: Đóng gói cấu hình Docker container khởi chạy an toàn với nhiều worker đồng thời

- [X] T015 Cập nhật lệnh khởi chạy trong `backend/Dockerfile` để hỗ trợ tham số `--workers ${UVICORN_WORKERS:-4}`
- [X] T016 [P] Cập nhật tệp cấu hình mẫu `.env.example` và thiết lập biến môi trường `UVICORN_WORKERS=4` cho dịch vụ backend trong `docker-compose.yml`

**Checkpoint**: Đã hoàn thành cấu hình môi trường Docker đa tiến trình.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Mục đích**: Hoàn thiện chất lượng mã nguồn, kiểm thử hồi quy và xác minh toàn diện

- [X] T017 Chạy toàn bộ bộ test suite backend bằng `pytest` (`backend/.venv/bin/pytest tests/unit/test_scheduler_coordinator.py tests/unit/test_auth_refresh.py`) để đảm bảo không có lỗi hồi quy (zero regressions)
- [X] T018 [P] Kiểm tra cú pháp, format và typing toàn bộ các tệp backend vừa chỉnh sửa bằng `ruff check backend/` và `ruff format --check backend/`
- [X] T019 Thực hiện xác minh các kịch bản thực tế theo hướng dẫn trong `specs/050-multi-worker-scheduler-lock/quickstart.md`

---

## Dependencies & Execution Order

### Thứ tự thực hiện các Phase:
1. **Setup (Phase 1)**: Bắt đầu ngay, không có phụ thuộc.
2. **Foundational (Phase 2)**: Phụ thuộc vào Setup hoàn thành - **BLOCKS** toàn bộ User Stories.
3. **User Stories (Phase 3 -> Phase 4)**:
   - **US1 (MVP)**: Phụ thuộc vào Phase 2.
   - **US2 (Failover)**: Phụ thuộc vào US1.
4. **Container Packaging (Phase 5)**: Phụ thuộc vào US1/US2.
5. **Polish (Phase 6)**: Phụ thuộc vào tất cả các phase trước.

### Cơ hội thực hiện song song (Parallel Execution):
- `T002` (docker-compose) và `T003` (Settings) có thể làm song song sau khi chỉnh `pyproject.toml`.
- `T006` (scheduler_types) có thể làm song song với `T004` (redis_client).
- `T007` (Unit test US1) có thể viết song song với thiết kế chi tiết logic.
- `T011` (Unit test US2) có thể viết song song với việc hoàn thiện US1.
- `T016` (.env.example) có thể làm song song với `T015`.
- `T018` (Linting ruff) có thể chạy độc lập.

---

## Implementation Strategy

### MVP First (Chỉ User Story 1):
1. Hoàn thành Phase 1 (Setup) và Phase 2 (Foundational).
2. Hoàn thành Phase 3 (User Story 1):
   - Đảm bảo 1 Leader duy nhất giành quyền và khởi động APScheduler.
   - Kiểm tra log và Redis key.
3. **Xác nhận MVP hoạt động**: Đã loại bỏ được 100% tình trạng nhân bản job scan khi tăng workers.

### Phát triển Tăng cường (Incremental Delivery):
1. Bổ sung User Story 2: Thêm Heartbeat và Standby polling -> Đạt khả năng tự phục hồi (Self-healing).
2. Hoàn thiện Container Packaging: Cập nhật Dockerfile và docker-compose.
3. Chạy Polish: Unit tests pass 100%, Ruff format chuẩn mực.
