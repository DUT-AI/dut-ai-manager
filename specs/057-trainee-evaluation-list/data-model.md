# Phase 1: Data Model & Contracts - Trainee Evaluation List

## 1. Data Contracts (Reused from OpenAPI / `meeting.types.ts`)

Không cần tạo entity mới, tận dụng 100% hợp đồng dữ liệu chuẩn hóa từ Backend:

```typescript
// Trích xuất từ Schema<'EvaluationResponse'>
export interface EvaluationResponse {
  id: number;
  meeting_id: number;
  reviewer_id?: number | null;
  target_user_id: number;
  evaluation_type: 'TRAINER_TO_TRAINEE' | 'TRAINEE_TO_TRAINER';
  is_anonymous: boolean;
  scores: EvaluationScoreItem[];
  average_score: number;
  feedback_text?: string | null;
  reviewer?: UserRef | null;
  target_user?: UserRef | null;
  created_at: string;
}

export interface EvaluationScoreItem {
  criteria_code: string;
  criteria_name: string;
  criteria_description: string;
  score: number;
}
```

## 2. Component View Models & States

### `TraineeEvaluationRowViewModel`
Dữ liệu hiển thị kết hợp giữa `ParticipantResponse` (học viên tham gia) và `EvaluationResponse` (bài đánh giá tương ứng):
```typescript
export interface TraineeEvaluationRow {
  participant: ParticipantResponse;
  evaluation?: EvaluationResponse | null;
  status: 'EVALUATED' | 'EVALUATED_ANONYMOUS' | 'NOT_EVALUATED' | 'ABSENT';
}
```

## 3. UI Contracts & Component Hierarchy

```text
MeetingDetailPage
├── MeetingHeroHeader
├── MeetingStatsRow
└── Tabs
    ├── Tab 'participants' (MeetingParticipantsTab)
    │   ├── MeetingBatchCheckInBanner
    │   ├── TrainerListTable
    │   ├── EvaluationProgressFilterBar (Bộ lọc: Tất cả | Đã đánh giá | Chưa đánh giá)
    │   └── TraineeListTable (Nâng cấp cột "Đánh giá": Cho phép click xem chi tiết bài đánh giá)
    │
    └── Tab 'evaluations' (MeetingEvaluationSummaryView)
        ├── MeetingOverallEvaluationCard
        ├── EvaluationOverviewCards
        ├── EvaluationCriteriaBreakdownCards
        ├── TraineeEvaluationListCard (MỚI: Bảng danh sách tất cả các Trainee đã đánh giá kèm điểm & nút xem chi tiết)
        └── EvaluationFeedbackListCard (Ý kiến đóng góp & Nhận xét)

Modal cấp trang (Mounted in MeetingDetailPage hoặc MeetingParticipantsTab):
└── EvaluationDetailModal (MỚI: Hiển thị chi tiết bài đánh giá bao gồm điểm từng tiêu chí, sao, feedback text)
```
