# Phase 0: Research - Trainee Evaluation List in Meeting Detail

## Problem Statement & Context
Người dùng muốn xem rõ ràng **Danh sách các Trainee đánh giá** tại giao diện chi tiết buổi học (`MeetingDetailPage`).
Hiện tại:
- Tab 1 ("Tham gia"): Có component `TraineeListTable` hiển thị cột "Đánh giá Giảng viên" dạng tag (`Đã gửi` / `Chưa gửi`), tuy nhiên:
  - Chưa cho phép click xem chi tiết từng tiêu chí điểm và feedback của Trainee đó đã chấm cho ai/điểm số ra sao.
  - Bộ lọc chưa tiện lợi và chưa gắn kết chặt chẽ với modal xem chi tiết.
- Tab 2 ("Báo cáo Đánh giá"): Hiển thị `EvaluationOverviewCards`, `EvaluationCriteriaBreakdownCards` và `EvaluationFeedbackListCard`. Tuy nhiên, phần `EvaluationFeedbackListCard` chỉ liệt kê danh sách nhận xét có văn bản (`feedback_text`), thiếu một **bảng tổng hợp danh sách Trainee đã nộp đánh giá** (kèm điểm số, ngày gửi, người được đánh giá, và nút xem chi tiết bài đánh giá).

## Feasibility & Architecture Fit
1. **Dữ liệu Backend sẵn có 100%**:
   - `GET /api/v1/meetings/{id}/evaluations/summary`: Đã trả về `evaluations: EvaluationResponse[]` chứa đầy đủ:
     - `evaluation_type`: `TRAINEE_TO_TRAINER` hoặc `TRAINER_TO_TRAINEE`.
     - `reviewer_id` & `reviewer`: UserRef của người đánh giá.
     - `target_user_id` & `target_user`: UserRef của người được đánh giá (Trainer).
     - `is_anonymous`: Boolean. Nếu `is_anonymous = true`, reviewer hiển thị là ẩn danh.
     - `average_score`: Điểm trung bình.
     - `scores`: Danh sách chi tiết điểm từng tiêu chí (`criteria_code`, `criteria_name`, `score`).
     - `feedback_text`: Nội dung nhận xét.
     - `created_at`: Mốc thời gian gửi đánh giá.
   - Do đó, **hoàn toàn KHÔNG cần thay đổi Backend** hoặc Database schema! Toàn bộ tính năng có thể triển khai sạch sẽ, an toàn trên Frontend.

2. **Frontend Component Architecture**:
   - Tuân thủ nghiêm ngặt **Principle VIII (Frontend Component Modularity)** trong Constitution:
     - Tách component xem chi tiết bài đánh giá thành modal độc lập: `EvaluationDetailModal.tsx`.
     - Tạo component chuyên trách hiển thị danh sách đánh giá Trainee trong Tab Báo cáo đánh giá: `TraineeEvaluationListCard.tsx`.
     - Nâng cấp `TraineeListTable.tsx` để hiển thị tương tác: Cho phép click vào tag hoặc nút "Xem đánh giá" để mở `EvaluationDetailModal`.
     - Tối ưu bộ lọc và thanh tiến độ trong `EvaluationProgressFilterBar.tsx` để Trainer dễ dàng lọc học viên đã/chưa đánh giá.

3. **Privacy & Anonymity (Ẩn danh)**:
   - Với các đánh giá ẩn danh (`is_anonymous = true`):
     - Xác nhận đã hoàn thành đánh giá cho Trainee (trên danh sách điểm danh).
     - Trong modal chi tiết đánh giá hoặc danh sách đánh giá, ẩn danh tính của người đánh giá (`Học viên ẩn danh`, avatar mặc định) để bảo đảm quyền riêng tư theo thiết kế của hệ thống.
