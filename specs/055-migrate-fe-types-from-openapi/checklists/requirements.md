# Checklist: Đặc tả Di chuyển Type OpenAPI Frontend

- [x] Có User Scenarios rõ ràng với tiêu chí nghiệm thu độc lập cho từng User Story.
- [x] Định rõ phạm vi (In Scope) và những việc không làm (Non-Goals).
- [x] Tuân thủ Hiến chương Điều XVI: Backend Pydantic là Single Source of Truth, không duplicate Zod cho API Response.
- [x] Cam kết chất lượng dài hạn: Không fix chắp vá, không dùng `as any`, không dùng `@ts-ignore`.
- [x] Đặt mục tiêu rõ ràng: `tsc -b` và `npm run build` đạt 0 lỗi 100%.
