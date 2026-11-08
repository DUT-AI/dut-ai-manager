# Quickstart & Verification Guide (Feature 055)

## 1. Sinh lại OpenAPI types từ Backend đang chạy
```bash
# Đảm bảo backend đang chạy ở cổng 8001
make backend-dev

# Tại frontend:
cd frontend
npm run generate:api
```

## 2. Kiểm tra tính toàn vẹn kiểu tĩnh toàn bộ Frontend
```bash
cd frontend
npx tsc -b
```
**Kỳ vọng**: Trả về 0 lỗi.

## 3. Chạy đóng gói Frontend Production Build
```bash
cd frontend
npm run build
```
**Kỳ vọng**: Lệnh `npm run build` thực thi thành công `tsc -b && vite build` và tạo thư mục `dist/`.
