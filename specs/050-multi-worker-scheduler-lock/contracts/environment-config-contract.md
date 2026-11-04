# Hợp Đồng Cấu Hình Môi Trường (Environment Configuration Contract)

**Feature**: `050-multi-worker-scheduler-lock`  
**Ngày**: 2026-11-05 (Đã tinh gọn: loại bỏ ENABLE_SCHEDULER)

---

## 1. Các Biến Môi Trường Mới Trong `Settings`

Tất cả các biến cấu hình được nạp thông qua Pydantic Settings (`app.core.config.Settings`):

| Tên biến | Kiểu dữ liệu | Giá trị mặc định | Mô tả |
| :--- | :--- | :--- | :--- |
| `REDIS_HOST` | `str` | `"localhost"` | Địa chỉ host của máy chủ Redis (trong Docker network: `"redis"`). |
| `REDIS_PORT` | `int` | `6379` | Cổng dịch vụ Redis. |
| `REDIS_PASSWORD` | `str` | `""` | Mật khẩu truy cập Redis (nếu có cấu hình). |
| `REDIS_DB` | `int` | `0` | Số thứ tự Database Redis sử dụng. |
| `UVICORN_WORKERS` | `int` | `4` | Số lượng worker process khởi chạy khi uvicorn phục vụ API. |

### Thuộc tính tính toán (Computed Properties)
- **`REDIS_URL`** (`str`):
  - Chuỗi kết nối đầy đủ cho Redis async client:
    - Nếu có password: `f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"`
    - Nếu không password: `f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"`

---

## 2. Cấu Hình Docker Compose (`docker-compose.yml`)

Dịch vụ Redis được định nghĩa với phiên bản gọn nhẹ `redis:7-alpine`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: dut-ai-redis
    restart: always
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - dut-ai-network

  backend:
    ...
    environment:
      - ENVIRONMENT=production
      - POSTGRES_SERVER=postgres
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - UVICORN_WORKERS=4
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ...

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

---

## 3. Cấu Hình `Dockerfile` Cho Multi-Worker

Tùy chỉnh lệnh khởi chạy trong `backend/Dockerfile` để hỗ trợ đa tiến trình worker:
- Lệnh chạy:
  ```dockerfile
  CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4}"]
  ```
- Mặc định 4 workers giúp xử lý đồng thời nhiều request API mà scheduler chỉ chạy duy nhất 1 lần.
