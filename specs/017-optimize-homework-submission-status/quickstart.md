# Quickstart & Verification Guide: Submission Status Optimization

## 1. Mục Tiêu Kiểm Chứng

Xác nhận endpoint `GET /api/v1/homeworks/{id}/submission-status` hoạt động siêu nhanh (< 100ms) và dữ liệu hiển thị trên frontend đầy đủ 100%.

## 2. Các Bước Kiểm Thử

### Bước 1: Kiểm thử Unit & Integration Tests của Backend
```bash
pytest backend/app/homework/tests/test_homework_api.py -v
```
Kỳ vọng: Tất cả các test cases liên quan đến submission status, homework detail đều pass.

### Bước 2: Kiểm thử thời gian phản hồi thực tế với Homework 72
```bash
# Đo thời gian phản hồi của endpoint
curl -o /dev/null -s -w 'Total time: %{time_total}s\nHTTP Status: %{http_code}\n' \
  -H "Authorization: Bearer <TOKEN>" \
  https://manage.dutai.io.vn/api/v1/homeworks/72/submission-status
```
Kỳ vọng:
- HTTP Status: `200`
- Total time: `< 0.2s` (giảm mạnh từ > 10.0s trước khi tối ưu).

### Bước 3: Kiểm thử giao diện người dùng
1. Mở trình duyệt đến `https://manage.dutai.io.vn/dashboard/homeworks/72`.
2. Kiểm tra danh sách học viên nộp bài hiển thị ngay tức thì, không bị treo spinner.
3. Bấm nút **"Đồng bộ từ Quiz"** để đảm bảo tính năng đồng bộ chủ động vẫn hoạt động chính xác khi cần.
