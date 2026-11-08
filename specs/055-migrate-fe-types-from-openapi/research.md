# Nghiên cứu Kiến trúc & Quyết định Kỹ thuật (Feature 055)

## 1. Vấn đề Enum trong TypeScript với flag `erasableSyntaxOnly: true`
- **Thực trạng**: Khi bật `"erasableSyntaxOnly": true` trong `tsconfig.app.json`, TypeScript 5.8+ nghiêm cấm cú pháp `enum` vì enum sinh ra mã JavaScript lúc runtime (không thể xóa bỏ đơn thuần kiểu type-only erasure).
- **Giải pháp chuẩn**: Dùng Object literal kết hợp `as const` và `typeof`:
  ```typescript
  export const BonusPointType = {
    CLUB_ACTIVITY: 'CLUB_ACTIVITY',
    OTHER: 'OTHER',
  } as const;
  export type BonusPointType = (typeof BonusPointType)[keyof typeof BonusPointType];
  ```
- **Lợi ích**: Giữ nguyên khả năng truy cập runtime `BonusPointType.CLUB_ACTIVITY`, tương thích 100% với `erasableSyntaxOnly` và bundler Vite/esbuild.

## 2. Xử lý trường `recent_users` trong `HomePage.tsx`
- **Thực trạng**: Component `HomePage.tsx` đang cố đọc `data?.recent_users` từ response của `reportService.getDashboardOverview(...)`. Tuy nhiên, schema Backend `DashboardOverviewResponse` chuẩn chỉ bao gồm:
  ```python
  class DashboardOverviewResponse(BaseModel):
      permission_requests: list[PermissionRequestResponse]
      bonus_points: list[BonusPointResponse]
      violations: list[ViolationResponse]
      unsubmitted_homeworks: list[HomeworkResponse]
      meetings: list[MeetingResponse]
  ```
  Không hề có trường `recent_users`.
- **Giải pháp chuẩn**:
  Tách `HomePage.tsx` thành 2 truy vấn riêng biệt:
  - Query 1: `getDashboardOverview` cho các chỉ số hoạt động.
  - Query 2: `userService.getUsers(1, 10)` qua React Query `['recent-users']` để hiển thị danh sách thành viên với kiểu dữ liệu chuẩn `UserResponse[]`.
- **Lợi ích**: Đúng với kiến trúc Backend, không giả mạo schema, hiển thị dữ liệu người dùng thật.

## 3. Khớp Envelope chuẩn giữa Backend và Frontend
- **Backend**:
  ```python
  class ApiResponse(BaseModel, Generic[T]):
      is_success: bool = True
      status_code: int = 200
      data: Optional[T] = None
      message: str = "Success"
      pagination: Optional[PaginationMeta] = None
  ```
- **Frontend legacy**: Một số hook như `useInAppNotifications.ts` cố truy cập `res.meta.total`.
- **Giải pháp**: Cập nhật sang `res.pagination?.total`.
