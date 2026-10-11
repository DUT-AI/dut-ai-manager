# Quickstart & Verification Guide: Đồng Nhất Kiến Trúc Phân Trang Giữa Frontend và Backend

**Feature Branch**: `009-unified-fe-be-pagination` | **Date**: 2026-10-10

---

## 1. Prerequisites & Environment Setup

Đảm bảo môi trường phát triển đã sẵn sàng:

```bash
# 1. Backend: Chạy kiểm tra môi trường ảo và pytest
cd /Users/nguyenhuynh/Documents/dut-ai-manager/backend
source venv/bin/activate  # hoặc conda activate nếu dùng anaconda
pytest tests/ -k pagination -v

# 2. Frontend: Kiểm tra TypeScript build
cd /Users/nguyenhuynh/Documents/dut-ai-manager/frontend
npm run build
```

---

## 2. Kịch Bản Kiểm Thử & Xác Nhận (Verification Scenarios)

### Kịch Bản 1: Kiểm tra Backend Phân Trang và Metadata (API Integration)

1. **Gọi API lấy trang 1 với kích thước 20**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/meetings?page=1&page_size=20" \
     -H "Authorization: Bearer <TOKEN>"
   ```
   **Kỳ vọng**:
   - `data`: Mảng có tối đa 20 phần tử.
   - `pagination.page = 1`.
   - `pagination.page_size = 20`.
   - `pagination.total`: Số lượng nguyên dương đại diện cho tổng số cuộc họp trong DB.
   - `pagination.total_pages`: Được tính tự động `ceil(total / 20)`.

2. **Gọi API với tham số không hợp lệ**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/meetings?page=0&page_size=200"
   ```
   **Kỳ vọng**:
   - HTTP Status: `422 Unprocessable Entity`.
   - Báo lỗi rõ ràng: `page` phải $\ge 1$ và `page_size` phải $\le 100$.

---

### Kịch Bản 2: Kiểm tra Phân Trang Ant Design Table và URL Sync (Frontend UI)

1. **Truy cập trang Quản lý Cuộc họp**: `http://localhost:5173/meetings`.
2. **Quan sát bảng Meeting Table**:
   - Hiển thị 20 dòng trên trang đầu tiên (`pageSize: 20`).
   - Góc dưới hiển thị dòng chữ tổng số: `1-20 của X bản ghi`.
   - Bộ chọn kích thước trang hiển thị các tùy chọn: `['10', '20', '50', '100']`.
3. **Chuyển sang trang 2**:
   - Bấm vào số "2" trên thanh phân trang.
   - URL thanh địa chỉ trình duyệt tự động cập nhật: `/meetings?page=2&pageSize=20`.
   - Bảng chuyển sang trạng thái loading và hiển thị các bản ghi từ 21 đến 40.
4. **Reload trang (F5)**:
   - Nhấn F5 để tải lại trang.
   - Trình duyệt vẫn giữ nguyên ở trang 2 với đúng dữ liệu của trang 2.

---

### Kịch Bản 3: Bảo Toàn Dữ Liệu Lịch và Dropdown Select

1. **Kiểm tra Lịch tuần (Calendar)**:
   - Truy cập trang Hoạt động Robot hoặc Lịch: `http://localhost:5173/robot-activity`.
   - Chọn tuần có nhiều hơn 20 cuộc họp.
   - Toàn bộ các cuộc họp trong tuần đều hiển thị đầy đủ trên giao diện tuần, không bị giới hạn cụt ở 20 bản ghi.
2. **Kiểm tra Dropdown Thành Viên**:
   - Mở Modal tạo cuộc họp hoặc giao bài tập.
   - Ô Select "Thành viên tham gia / Học viên" tải dữ liệu từ `/users/options`.
   - Toàn bộ học viên active đều xuất hiện trong danh sách tìm kiếm/chọn.

---

### Kịch Bản 4: Kiểm tra Tính Tương Thích Ngược của Zalo Mini App

1. Trong thư mục `zalo-mini-app/`:
   ```bash
   cd /Users/nguyenhuynh/Documents/dut-ai-manager/zalo-mini-app/dut-manager
   npm run build
   ```
2. Kiểm tra không có lỗi biên dịch TypeScript.
3. Khi gọi API `meetingService.getMeetings(1, 20)`, hàm trích xuất `response.data.data` vẫn trả về mảng danh sách hợp lệ và hiển thị danh sách cuộc họp trơn tru trên mobile interface.
