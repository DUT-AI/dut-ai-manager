# Kế hoạch Triển khai: Tinh giản Đánh giá Meeting & Chuẩn hóa Kiến trúc Full Stack

**Branch**: `046-harden-meeting-evaluation` | **Ngày lập**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Đặc tả tính năng từ `/specs/046-harden-meeting-evaluation/spec.md` và các quyết định kiến trúc trong [research.md](./research.md).

---

## 1. Tóm tắt Kế hoạch (Summary)

Kế hoạch này tập trung vào 3 trụ cột kỹ thuật cốt lõi:
1. **Tinh giản mô hình Đánh giá**: Bỏ hoàn toàn luồng Trainer chấm điểm từng Trainee cá nhân (`TRAINER_TO_TRAINEE`). Trainer chỉ thực hiện Đánh giá tổng thể toàn bộ buổi học (`MeetingOverallEvaluation`) theo 4 tiêu chí chuẩn. Trainee tiếp tục đánh giá Trainer phụ trách (`TRAINEE_TO_TRAINER`).
2. **Siết chặt Domain Invariants**: Bổ sung cơ chế chống tự đánh giá bản thân (`reviewer_id == target_user_id` trả về 400), xác thực người nhận đánh giá bắt buộc phải là Trainer của buổi học, và xác thực người gửi đánh giá tổng thể phải có thẩm quyền Trainer/Creator/Admin.
3. **Chuẩn hóa Chất lượng Code, Hiến pháp & Trải nghiệm (Code Quality & UX)**:
   - Sửa vi phạm Điều XIV của Hiến pháp (No Fake Optionals) trong `GetMeetingEvaluationSummaryUseCase`: Biến `overall_eval_repo: MeetingOverallEvaluationRepository` thành tham số bắt buộc.
   - Loại bỏ truy vấn lặp trong cơ sở dữ liệu: Giảm 50% số lượng query `meeting` ở luồng nộp đánh giá tổng thể bằng cách chuyển permission invariants vào Use Case.
   - Hiển thị mốc thời gian hạn chót đánh giá (`evaluation_deadline`) rõ ràng trên giao diện `MeetingHeroHeader`.
   - Dọn sạch mã nguồn frontend: Xóa bỏ component `TrainerEvaluationModal.tsx` và các nút bấm chấm điểm từng dòng học viên trong `TraineeListTable.tsx` / `ParticipantActionButtons.tsx`.
4. **Loại bỏ Dead Code, Component Mồ côi & Tinh giản Báo cáo Đánh giá (Dead Code Elimination & Refactoring)**:
   - Xóa bỏ toàn bộ các file mồ côi: `ParticipantListModal.tsx`, `ParticipantListTable.tsx`, `MeetingTraineeEvaluationBanner.tsx`.
   - Xóa bỏ modal tàn dư `MyEvaluationResultModal.tsx` và các nút "Điểm của tôi" / "Xem Điểm của tôi" trên Header, Card, Tab và Page.
   - Xóa bỏ dead code ở Backend: `SubmitTrainerEvaluationUseCase.py`, unregister khỏi DI container, xóa DTO `TrainerSubmitEvaluationRequest` và các import thừa trong `evaluation_controller.py`.
   - Dọn sạch hooks và services thừa: `useMyEvaluationResult`, `meetingService.submitTrainerEvaluation`, `meetingService.getMyEvaluationResult`, `TrainerSubmitEvaluationPayload`, `canEvaluateTrainee`, và prop thừa `isEnded` trong `ParticipantActionButtons.tsx`.
   - Tinh giản Tab Báo cáo Đánh giá: Ẩn cột/card "Trainer đánh giá Trainee" khi không có dữ liệu để không gây hiểu nhầm.

---

## 2. Bối cảnh Kỹ thuật (Technical Context)

- **Ngôn ngữ & Phiên bản**: Python 3.12+ (Backend), TypeScript 5.x / React 19 (Frontend).
- **Thư viện / Framework cốt lõi**:
  - Backend: FastAPI, SQLAlchemy 2.0, Dishka DI, Pydantic V2, Pytest.
  - Frontend: React 19, Vite, Ant Design (antd) 5.x, React Query (@tanstack/react-query), Tailwind CSS.
- **Cơ sở dữ liệu & Lưu trữ**: PostgreSQL (`TIMESTAMPTZ` cho toàn bộ các mốc thời gian UTC), SQLAlchemy ORM.
- **Kiểm thử tự động**: Pytest (Backend unit & integration tests), TypeScript Compiler (`npx tsc --noEmit`).
- **Nền tảng đích**: Web Application (Linux Server / Docker Production).
- **Mục tiêu hiệu năng & Ràng buộc**:
  - Thời gian xử lý API đánh giá < 150ms.
  - Số lượng truy vấn DB cho mỗi request đánh giá: Tối đa 1 query `Meeting` aggregate.
  - Tuân thủ 100% 14 Điều của Hiến pháp dự án DUT AI Manager.

---

## 3. Đánh giá Hiến pháp (Constitution Check)

*GATE: Toàn bộ các nguyên tắc sau đã được rà soát và đáp ứng:*

| Nguyên tắc | Mô tả quy định | Trạng thái | Đánh giá tuân thủ trong tính năng |
|---|---|:---:|---|
| **I. Clean Architecture & DDD** | Phân tầng Domain, Application, Infrastructure, Presentation rõ ràng | **PASS** | Logic nghiệp vụ chống tự đánh giá và thẩm quyền nằm ở Domain/Use Case; không rò rỉ SQL ra ngoài Repository. |
| **II. Dishka DI** | Tiêm phụ thuộc qua Dishka Provider | **PASS** | Mọi Repository và Use Case đều được cấu hình trong `MeetingModuleProvider`. |
| **III. Enterprise UTC Storage** | Lưu trữ UTC chuẩn hóa, múi giờ VN hiển thị | **PASS** | Sử dụng `datetime.now(UTC)` và `UtcDateTime` cho `evaluation_deadline`. |
| **VII. Single-Responsibility Use Cases** | 1 use case = 1 file = 1 public method `execute()` | **PASS** | Các use case `SubmitTraineeEvaluationUseCase`, `SubmitMeetingOverallEvaluationUseCase`, `GetMeetingEvaluationSummaryUseCase` tuân thủ nghiêm ngặt. |
| **VIII. Frontend Modularity** | Không viết modal monolithic, phân tách subcomponents | **PASS** | Dọn dẹp modal thừa `TrainerEvaluationModal`, sử dụng các subcomponents chuyên biệt trong `components/participants/`. |
| **X. Zero Redundant Wrappers** | Không tạo alias hoặc bọc tương thích thừa | **PASS** | Xóa bỏ dứt khoát modal và luồng Trainer chấm cá nhân thừa, không giữ code bọc tương thích rác. |
| **XIV. No Fake Optionals** | Không sử dụng `Type \| None = None` cho collaborator bắt buộc | **PASS** | `GetMeetingEvaluationSummaryUseCase` sửa `overall_eval_repo` thành non-nullable bắt buộc; xóa `if self.overall_eval_repo:`. |

---

## 4. Cấu trúc Dự án (Project Structure)

### 4.1. Tài liệu Thiết kế (`specs/046-harden-meeting-evaluation/`)

```text
specs/046-harden-meeting-evaluation/
├── spec.md              # Đặc tả yêu cầu người dùng
├── plan.md              # Kế hoạch triển khai kiến trúc (Tài liệu này)
├── research.md          # Kết quả nghiên cứu kỹ thuật & quyết định kiến trúc
├── data-model.md        # Mô hình thực thể & Domain Invariants
├── contracts/           # API Contract OpenAPI 3.1
│   └── meeting-evaluation-api.yaml
├── quickstart.md        # Hướng dẫn chạy & kiểm thử nghiệm thu
└── checklists/
    └── requirements.md  # Checklist thẩm định Spec
```

### 4.2. Mã nguồn triển khai (Source Code Layout)

```text
backend/app/meeting/
├── application/
│   ├── get_meeting_evaluation_summary_use_case.py   # Sửa Fake Optional (Điều XIV)
│   ├── submit_trainee_evaluation_use_case.py        # Thêm invariant chống tự đánh giá
│   ├── submit_meeting_overall_evaluation_use_case.py # Thêm invariant kiểm tra quyền Trainer/Admin
│   ├── submit_trainer_evaluation_use_case.py        # Vô hiệu hóa / dọn dẹp
│   └── get_my_evaluation_result_use_case.py         # Giản lược an toàn
├── controllers/
│   ├── dependencies.py                              # Tối ưu logic quyền sở hữu
│   └── evaluation_controller.py                     # Bỏ Depends thừa, tối ưu 1 query
└── domain/
    ├── entity.py                                    # Domain Entity Meeting & Evaluations
    └── participant.py                               # Kiểm tra 0 dead code, tiếng Việt có dấu

frontend/src/features/meeting/
├── components/
│   ├── MeetingHeroHeader.tsx                        # Hiển thị evaluation_deadline
│   ├── MeetingParticipantsTab.tsx                   # Bỏ mapping trainerEvalsByTraineeId
│   ├── ParticipantActionButtons.tsx                 # Bỏ nút chấm điểm học viên cá nhân
│   ├── TrainerEvaluationModal.tsx                   # XÓA BỎ HOÀN TOÀN
│   ├── index.ts                                     # Dọn dẹp export TrainerEvaluationModal
│   └── participants/
│       ├── TraineeListTable.tsx                     # Bỏ cột và props chấm điểm cá nhân
│       ├── TraineeEvaluationCard.tsx                # Tinh giản thông điệp đánh giá Trainer
│       └── EvaluationProgressFilterBar.tsx          # Chỉ hiển thị tiến độ học viên đánh giá
└── types/
    └── meeting.types.ts                             # Giữ sạch sẽ UserRef và schemas
```

---

## 5. Theo dõi Độ phức tạp (Complexity Tracking)

*Không có vi phạm Hiến pháp cần biện minh. Toàn bộ thiết kế đều tuân thủ và làm giảm độ phức tạp của hệ thống (xóa bỏ 1 modal thừa, xóa bỏ 1 flow đánh giá cá nhân lặp lại, tối ưu 1 truy vấn cơ sở dữ liệu).*
