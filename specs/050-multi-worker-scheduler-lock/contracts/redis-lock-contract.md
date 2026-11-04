# Hợp Đồng Giao Thức: Khóa Phân Tán Redis (Redis Lock Contract)

**Feature**: `050-multi-worker-scheduler-lock`  
**Ngày**: 2026-11-05

---

## 1. Chi Tiết Lệnh Redis (Redis Commands Specification)

Bộ điều phối tác vụ nền tương tác với Redis qua 3 thao tác cơ bản tuân thủ tính nguyên tử (atomic operations):

### 1.1 Chiếm Khóa (Acquire Lock)
- **Lệnh**: `SET dut_ai:scheduler:leader_lock <worker_id> NX EX 30`
- **Ý nghĩa tham số**:
  - `NX`: Chỉ thiết lập nếu key CHƯA tồn tại.
  - `EX 30`: Đặt thời gian hết hạn là 30 giây.
- **Giá trị trả về**:
  - `True / OK`: Chiếm khóa thành công. Tiến trình trở thành **LEADER**.
  - `False / None`: Khóa đang được một tiến trình khác nắm giữ. Tiến trình trở thành **STANDBY**.

### 1.2 Duy Trì Khóa (Renew Lock / Heartbeat)
- **Chu kỳ thực thi**: Mỗi 10 giây (khi đang là LEADER).
- **Lệnh Lua Script Nguyên Tử**:
  ```lua
  if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("expire", KEYS[1], ARGV[2])
  else
      return 0
  end
  ```
- **Tham số**:
  - `KEYS[1]`: `dut_ai:scheduler:leader_lock`
  - `ARGV[1]`: `<worker_id>`
  - `ARGV[2]`: `30` (TTL mới tính bằng giây)
- **Giá trị trả về**:
  - `1`: Gia hạn thành công.
  - `0`: Thất bại (Khóa đã bị mất hoặc bị ghi đè bởi worker khác). Nếu nhận giá trị `0`, Leader lập tức dừng `APScheduler` và hạ cấp về vai trò `STANDBY`.

### 1.3 Giải Phóng Khóa An Toàn (Release Lock)
- **Kích hoạt khi**: Tiến trình Leader nhận tín hiệu tắt ứng dụng (`lifespan` shutdown).
- **Lệnh Lua Script Nguyên Tử**:
  ```lua
  if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
  else
      return 0
  end
  ```
- **Tham số**:
  - `KEYS[1]`: `dut_ai:scheduler:leader_lock`
  - `ARGV[1]`: `<worker_id>`
- **Giá trị trả về**:
  - `1`: Xóa khóa thành công, cho phép các standby worker tranh chấp ngay lập tức.
  - `0`: Bỏ qua xóa vì khóa hiện tại không thuộc sở hữu của tiến trình này.

---

## 2. Giao Thức Đảm Bảo Không Lỗi (Exception Handling Protocol)

1. **RedisConnectionError / RedisTimeoutError**:
   - Nếu xảy ra lỗi kết nối mạng tới Redis trong quá trình chạy:
     - Ghi log mức độ `WARNING`: `⚠️ [SchedulerCoordinator] Redis connection lost. Retrying in 10s...`
     - Tuyệt đối **KHÔNG** raise Exception làm sập tiến trình FastAPI / Uvicorn.
     - Luồng Web API tiếp tục phục vụ các yêu cầu HTTP từ client bình thường.
     - Lần thăm dò tiếp theo sẽ thử kết nối lại tự động.
2. **Leader Thất Lạc Khóa (Lost Leadership)**:
   - Nếu Leader không thể gửi heartbeat sau 30 giây (hoặc nhận kết quả `0` từ Redis), Leader phải chủ động gọi `scheduler.shutdown(wait=False)` để ngăn chặn tình trạng "Split-Brain" (hai leader chạy song song).
