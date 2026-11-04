# Nghiên Cứu Kiến Trúc: Điều Phối Tác Vụ Nền Đa Tiến Trình (Multi-Worker Scheduler Synchronization)

**Feature**: `050-multi-worker-scheduler-lock`  
**Ngày**: 2026-11-05  
**Trạng thái**: Hoàn thành nghiên cứu kỹ thuật (Đã tinh gọn: loại bỏ ENABLE_SCHEDULER theo yêu cầu)

---

## 1. Bối Cảnh & Vấn Đề Kỹ Thuật

Hiện tại, máy chủ FastAPI (`dut-ai-manager/backend`) sử dụng `APScheduler` (`AsyncIOScheduler`) được khởi động trong hàm `lifespan` tại `app/main.py`.
Khi nâng số lượng worker trong `uvicorn` (ví dụ: `uvicorn --workers 4` trong Dockerfile):
- Mỗi tiến trình worker là một process Python độc lập với bộ nhớ riêng biệt.
- Mỗi worker đều thực thi hàm `lifespan` lúc khởi động và tự kích hoạt 1 bản sao `AsyncIOScheduler`.
- Hậu quả: 7 tác vụ quét định kỳ (quét deadline bài tập, điểm danh meeting, nhắc việc, tính điểm...) bị kích hoạt đồng thời $N$ lần trên $N$ workers, gây ra hiện tượng nhân bản thông báo (spam Zalo/Discord/Web Push) và xung đột ghi dữ liệu trong cơ sở dữ liệu.

---

## 2. Quyết Định Kiến Trúc (Architecture Decisions)

### Quyết định 1: Cơ chế Bầu chọn Thủ lĩnh Tự Động (Automatic Leader Election) trên Redis
- **Giải pháp được chọn**: Sử dụng Redis làm Distributed Lock / Leader Election trung tâm.
- **Nguyên lý hoạt động tự động (Zero-Config)**: Mọi worker khi khởi động đều mặc định kết nối Redis và tham gia tranh chấp quyền Leader. Không cần cờ cấu hình bật/tắt thủ công (`ENABLE_SCHEDULER`).
- **Lý do lựa chọn**:
  - Tách biệt hoàn toàn tải khóa ra khỏi cơ sở dữ liệu quan hệ PostgreSQL chính. Thao tác kiểm tra khóa và heartbeat diễn ra cực nhanh trên bộ nhớ RAM (độ trễ <1ms).
  - Lệnh nguyên tử của Redis (`SET key value NX EX ttl`) cung cấp sự đảm bảo tuyệt đối về tính nguyên tử (atomic), không bao giờ có 2 worker cùng thắng khóa tại một thời điểm, kể cả trong trường hợp khởi động đồng thời (cold start).
  - Mở đường hạ tầng vững chắc cho các bài toán tiếp theo của dự án: Caching API (phòng họp, dữ liệu danh mục), Rate Limiting (chống DDoS đăng nhập), Token Blacklist và Message/Task Queue (BullMQ/ARQ/Celery).

### Quyết định 2: Chu kỳ Khóa (TTL), Heartbeat Loop và Failover Standby Loop
- **Giải pháp được chọn**:
  - **Khóa Leader**: Key `dut_ai:scheduler:leader_lock`, giá trị là `worker_id` (ví dụ: `worker_{hostname}_{pid}_{uuid}`).
  - **Thời gian sống của khóa (TTL)**: 30 giây (`EX 30`).
  - **Chu kỳ Heartbeat (Leader)**: 10 giây một lần. Khi worker còn là Leader, nó thực hiện gia hạn `EXPIRE 30` cho key.
  - **Chu kỳ Thăm dò (Standby Workers)**: 10 giây một lần. Các worker không giành được khóa sẽ chạy một background task nhẹ (`asyncio.sleep(10)`). Khi khóa hết hạn (do leader cũ bị crash, bị kill hoặc ngắt mạng quá 30 giây), các worker standby sẽ lập tức tranh chấp lại khóa bằng `SET ... NX EX 30`.
  - **Thời gian Failover tối đa**: Dưới 40 giây (30s TTL hết hạn + tối đa 10s chu kỳ thăm dò), thỏa mãn tiêu chí thành công SC-004 (<60s).
- **Lý do lựa chọn**:
  - Tỷ lệ 1:3 giữa chu kỳ Heartbeat (10s) và TTL (30s) là chuẩn công nghiệp (tương tự như Raft/ZooKeeper/Consul), đảm bảo nếu có mạng chập chờn 1 chu kỳ thì khóa vẫn không bị mất nhầm.

### Quyết định 3: Thư viện Client & Tích hợp Dependency Injection
- **Giải pháp được chọn**: Sử dụng thư viện `redis>=5.0.0` (chính thức từ Redis, hỗ trợ `redis.asyncio` native).
- **Tích hợp Dishka DI**:
  - Đăng ký `redis.asyncio.ConnectionPool` và `redis.asyncio.Redis` vào `InfrastructureProvider` (`app/shared/providers.py`) với `Scope.APP`.
  - Giúp tái sử dụng kết nối Redis xuyên suốt toàn bộ ứng dụng và phục vụ DI cho các feature khác sau này.

### Quyết định 4: Giải phóng Khóa An toàn (Safe Release) bằng Lua Script
- **Giải pháp được chọn**:
  - Khi Leader shutdown bình thường (trong `lifespan` shutdown), nó PHẢI giải phóng khóa ngay lập tức để worker khác có thể tiếp quản tức thì mà không phải chờ hết 30 giây TTL.
  - Tuy nhiên, để tránh giải phóng nhầm khóa nếu worker bị pause quá lâu và khóa đã thuộc về worker khác, việc giải phóng bắt buộc dùng Lua script nguyên tử:
    ```lua
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    ```
- **Lý do lựa chọn**: Ngăn chặn race condition nghiêm trọng khi xóa nhầm khóa của Leader kế nhiệm.

### Quyết định 5: Bảo vệ Tác Vụ Chạy Chồng Chéo (Overlapping Protection)
- **Giải pháp được chọn**:
  - APScheduler được cấu hình với job defaults: `max_instances=1`, `coalesce=True`, `misfire_grace_time=300`.
  - Nếu một tác vụ quét dữ liệu kéo dài hơn chu kỳ định sẵn, APScheduler sẽ tự động bỏ qua lần chạy tiếp theo thay vì chạy song song 2 tác vụ cùng loại, đáp ứng trọn vẹn yêu cầu FR-005.

### Quyết định 6: Cấu hình Môi trường Tinh Gọn (Zero Bloat)
- **Giải pháp được chọn**:
  - Chỉ bổ sung cấu hình kết nối Redis tối thiểu trong `Settings`:
    - `REDIS_HOST: str = "localhost"`
    - `REDIS_PORT: int = 6379`
    - `REDIS_PASSWORD: str = ""`
    - `REDIS_DB: int = 0`
    - `UVICORN_WORKERS: int = 4` (Số lượng worker khởi chạy trong container)
  - Cập nhật `docker-compose.yml`:
    - Thêm service `redis: 7-alpine` với healthcheck và volume lưu dữ liệu.
    - Cấu hình mạng `dut-ai-network` dùng chung cho `postgres`, `redis`, `backend`, `frontend`.
  - Cập nhật `backend/Dockerfile`:
    - Khởi chạy uvicorn với `--workers ${UVICORN_WORKERS:-4}`.

---

## 3. Đánh Giá Khả Năng Chịu Lỗi (Fault Tolerance & Graceful Degradation)

| Kịch bản sự cố | Hành vi hệ thống | Kết quả |
| :--- | :--- | :--- |
| **Redis bị ngắt kết nối khi khởi động** | Log cảnh báo `WARNING`. Không làm sập tiến trình Web API. Standby loop áp dụng exponential backoff để thử kết nối lại. | Hệ thống vẫn phục vụ HTTP API bình thường (FR-006). |
| **Worker Leader bị Kill / OOM** | Khóa tự động hết hạn sau 30 giây TTL trên Redis. Standby worker khác giành được khóa và khởi động APScheduler. | Tự phục hồi không cần can thiệp thủ công (SC-004). |
| **Tất cả các worker cùng tranh chấp lúc khởi động** | Lệnh `SET NX` nguyên tử của Redis chỉ trả về `True` cho duy nhất 1 worker. Các worker còn lại nhận `False` và chuyển sang chế độ Standby. | 0% xung đột kép (SC-001, SC-002). |
| **Leader khởi động lại tham gia lại cụm** | Nhận `False` khi cố lấy khóa vì đang có Leader khác hoạt động. Nó tự động trở thành Standby worker phục vụ API. | Hoạt động trơn tru (US2 Scenario 2). |
