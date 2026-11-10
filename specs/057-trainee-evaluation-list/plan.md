# Implementation Plan: Trainee Evaluation List in Meeting Detail

**Branch**: `057-trainee-evaluation-list` | **Date**: 2026-11-10 | **Spec**: [specs/057-trainee-evaluation-list/spec.md](specs/057-trainee-evaluation-list/spec.md)

**Input**: Feature specification from `specs/057-trainee-evaluation-list/spec.md`

## Summary

Triển khai tính năng hiển thị trực quan và chi tiết **Danh sách các Trainee đánh giá** tại giao diện Chi tiết Buổi học (`MeetingDetailPage`).
- **Tab Tham gia (`TraineeListTable`)**: Bổ sung tương tác click vào trạng thái đánh giá để mở Modal xem chi tiết bài đánh giá (`EvaluationDetailModal`).
- **Tab Báo cáo Đánh giá (`MeetingEvaluationSummaryView`)**: Bổ sung component thẻ danh sách học viên đánh giá (`TraineeEvaluationListCard`), hiển thị danh sách các Trainee đã hoàn thành đánh giá, điểm trung bình, người được đánh giá và nút xem nhanh chi tiết.
- **Tận dụng 100% dữ liệu API hiện có**: Không yêu cầu sửa đổi backend hay cơ sở dữ liệu.

## Technical Context

**Language/Version**: TypeScript 5.x / React 19 / Python 3.12 (Backend unchanged)  
**Primary Dependencies**: Ant Design (Antd), Dayjs, React Query, Lucide/Antd Icons  
**Storage**: N/A (Client UI enhancement)  
**Testing**: `npx tsc -b` (Frontend strict type check), `npm run build` (Vite build)  
**Target Platform**: Web Browser & Mobile Responsive (iOS/Android responsive layouts)  
**Project Type**: Web Application Frontend (`frontend/src/features/meeting/`)  
**Performance Goals**: Instant UI rendering (< 100ms response time khi mở modal/filter)  
**Constraints**: Bảo vệ tính ẩn danh của học viên nếu `is_anonymous = true`  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Hiến pháp | Trạng thái | Đánh giá tuân thủ |
|---|---|---|
| **VIII. Frontend Component Modularity & Single-Responsibility UI** | PASS | Tách `EvaluationDetailModal` và `TraineeEvaluationListCard` thành các component độc lập tại `frontend/src/features/meeting/components/`. |
| **X. Zero Redundant Backward Compatibility** | PASS | Sử dụng trực tiếp các interface hiện hữu trong `meeting.types.ts`, không tạo alias hay wrapper thừa. |
| **XVI. Single Source of Truth API Contracts** | PASS | Sử dụng các type được đồng bộ từ OpenAPI (`EvaluationResponse`, `ParticipantResponse`). |
| **XVII. Strongly-Typed Storage & Zero Raw Dictionaries** | PASS | Sử dụng strictly typed props và state, không dùng `any` hay raw dicts. |

## Project Structure

### Documentation (this feature)

```text
specs/057-trainee-evaluation-list/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 research output
└── data-model.md        # Phase 1 UI data model & layout
```

### Source Code Changes

```text
frontend/src/features/meeting/
├── components/
│   ├── EvaluationDetailModal.tsx              # [NEW] Modal hiển thị chi tiết điểm tiêu chí & nhận xét bài đánh giá
│   ├── summary/
│   │   ├── TraineeEvaluationListCard.tsx      # [NEW] Danh sách các Trainee đã đánh giá trong tab Báo cáo
│   │   └── index.ts                           # Re-export TraineeEvaluationListCard
│   ├── participants/
│   │   ├── TraineeListTable.tsx               # [UPDATE] Cho phép click xem chi tiết bài đánh giá
│   │   └── ParticipantMobileList.tsx          # [UPDATE] Hiển thị nhãn đánh giá tương tác trên Mobile
│   ├── MeetingParticipantsTab.tsx             # [UPDATE] Quản lý state mở EvaluationDetailModal từ bảng học viên
│   ├── MeetingEvaluationSummaryView.tsx       # [UPDATE] Tích hợp TraineeEvaluationListCard vào tab Báo cáo
│   └── index.ts                               # Re-export EvaluationDetailModal
```

## Detailed Execution Steps

### Step 1: Tạo `EvaluationDetailModal.tsx`
- Xây dựng component modal hiển thị:
  - Header: Tên người đánh giá (hoặc "Học viên ẩn danh" nếu `is_anonymous`), Avatar, Role tag, mốc thời gian.
  - Target: Người được đánh giá (Trainer).
  - Điểm tổng quan: Rate sao và số điểm trung bình (`average_score.toFixed(1)`).
  - Bảng/Danh sách tiêu chí: Liệt kê các tiêu chí con (`criteria_name`, `criteria_description`, `score`).
  - Ý kiến đóng góp: Hiển thị `feedback_text` (nếu có).

### Step 2: Tạo `TraineeEvaluationListCard.tsx`
- Đặt tại `frontend/src/features/meeting/components/summary/TraineeEvaluationListCard.tsx`.
- Lọc danh sách `evaluations` có `evaluation_type === 'TRAINEE_TO_TRAINER'`.
- Hiển thị Antd Table/List gọn gàng:
  - Cột Học viên (Avatar + Tên hoặc "Ẩn danh").
  - Cột Giảng viên được đánh giá.
  - Cột Điểm trung bình (sao + tag điểm).
  - Cột Ngày gửi (`DD/MM/YYYY HH:mm`).
  - Cột Thao tác: Nút "Xem chi tiết" mở `EvaluationDetailModal`.

### Step 3: Nâng cấp `TraineeListTable.tsx` & `ParticipantMobileList.tsx`
- Nhận thêm prop `onViewEvaluation?: (evaluation: EvaluationResponse) => void`.
- Cột "Đánh giá Giảng viên": Nếu học viên đã đánh giá, Tag trạng thái biến thành clickable tag hoặc kèm nút icon con mắt để Trainer có thể click xem bài đánh giá trực tiếp.

### Step 4: Tích hợp và Quản lý State tại `MeetingParticipantsTab.tsx` & `MeetingEvaluationSummaryView.tsx`
- Đặt `EvaluationDetailModal` vào cả hai tab hoặc nâng lên cấp trang để tái sử dụng mượt mà.
- Kiểm tra quyền truy cập (nếu là Trainee chỉ xem được đánh giá của chính mình, Trainer/Admin xem được danh sách).

### Step 5: Kiểm tra Typecheck và Build Production
- Chạy `npx tsc -b` trong `frontend/`.
- Chạy `npm run build` để kiểm tra đóng gói.
