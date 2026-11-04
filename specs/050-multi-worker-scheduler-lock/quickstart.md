# Hướng Dẫn Kiểm Thử & Xác Minh Tính Năng (Quickstart Validation Guide)

**Feature**: `050-multi-worker-scheduler-lock`  
**Ngày**: 2026-11-05 (Đã tinh gọn)

---

## 1. Yêu Cầu Tiên Quyết (Prerequisites)

1. Máy chủ có cài đặt Python 3.12 và môi trường ảo `backend/.venv`.
2. Dịch vụ Redis đang chạy (qua Docker hoặc cục bộ trên cổng `6379`).
   - Kiểm tra Redis: `redis-cli ping` (kết quả trả về `PONG`).
3. Dịch vụ PostgreSQL đang hoạt động.

---

## 2. Kịch Bản Kiểm Thử & Xác Minh (Validation Scenarios)

### Kịch Bản 1: Khởi động Đa Tiến Trình (Multi-Worker) - Xác Minh Duy Nhất 1 Leader (US1)

**Mục tiêu**: Chứng minh khi khởi chạy 4 workers, chỉ có duy nhất 1 worker kích hoạt APScheduler, 3 workers còn lại ở chế độ Standby.

1. **Lệnh chạy**:
   ```bash
   cd backend
   .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
   ```

2. **Kết quả mong đợi trong Log**:
   - Xuất hiện 4 tiến trình worker khởi động độc lập.
   - Duy nhất **1 worker** ghi log:
     ```text
     👑 [SchedulerCoordinator] Worker <worker_id_1> acquired LEADER lock. Starting APScheduler...
     📅 Starting background scheduler...
     📅 Scheduler started - Homework & Meeting check at 23:59 daily, Evaluations hourly
     ```
   - 3 worker còn lại ghi log:
     ```text
     🛡️ [SchedulerCoordinator] Worker <worker_id_x> is in STANDBY mode (Leader is active).
     ```
   - Kiểm tra key trên Redis:
     ```bash
     redis-cli get dut_ai:scheduler:leader_lock
     # Kết quả trả về: worker_id_1
     redis-cli ttl dut_ai:scheduler:leader_lock
     # Kết quả luôn dao động trong khoảng 20s - 30s nhờ Heartbeat định kỳ 10s
     ```

---

### Kịch Bản 2: Kiểm Thử Tự Phục Hồi & Chuyển Giao Quyền (Failover) (US2)

**Mục tiêu**: Chứng minh khi tiến trình Leader bị tắt đột ngột, một trong các Standby worker sẽ tự động tiếp quản vai trò Leader trong vòng dưới 40 giây.

1. **Thao tác**:
   - Xác định PID của Worker đang giữ quyền Leader từ log hoặc từ giá trị `redis-cli get dut_ai:scheduler:leader_lock`.
   - Giả lập sự cố bằng cách cưỡng chế dừng tiến trình Leader:
     ```bash
     kill -9 <LEADER_PID>
     ```

2. **Kết quả mong đợi trong Log**:
   - Uvicorn master process sinh ra worker mới thay thế tiến trình bị kill.
   - Sau khi TTL 30 giây hết hạn (hoặc ngay khi khóa được giải phóng):
     ```text
     👑 [SchedulerCoordinator] Worker <worker_id_standby> successfully acquired LEADER lock after failover! Starting APScheduler...
     📅 Starting background scheduler...
     📅 Scheduler started...
     ```
   - Các tác vụ nền tiếp tục hoạt động bình thường mà không bị đình trệ hay nhân bản.

---

### Kịch Bản 3: Chạy Bộ Kiểm Thử Tự Động (Automated Test Suite)

Chạy kiểm thử đơn vị cho Coordinator và Redis Lock:
```bash
cd backend
.venv/bin/pytest tests/unit/test_scheduler_coordinator.py -v
```
**Kết quả mong đợi**: Toàn bộ unit tests bao phủ các kịch bản (Leader win, Standby poll, Heartbeat renew, Safe release, Redis failover) đều ĐẠT (PASS).
