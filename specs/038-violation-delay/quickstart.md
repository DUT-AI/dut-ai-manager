# Phase 1: Quickstart & Verification Guide (038-violation-delay)

Tài liệu này hướng dẫn cách chạy và kiểm thử nghiệm thu toàn bộ tính năng lùi thời gian kiểm tra vi phạm thêm 2 ngày.

---

## 1. Môi trường Thực thi (Prerequisites)

- Sử dụng virtual environment của backend: `backend/.venv/bin/pytest` và `backend/.venv/bin/python`.
- Đảm bảo terminal đang ở thư mục gốc của dự án (`/Users/nguyenhuynh/Documents/dut-ai-manager`).

---

## 2. Kiểm thử Tự động (Automated Unit Tests)

Chạy bộ unit test chuyên biệt cho 4 use case kiểm tra vi phạm:

```bash
backend/.venv/bin/pytest \
  backend/tests/unit/test_homework_checker.py \
  backend/tests/unit/test_meeting_use_cases.py \
  backend/tests/unit/test_duty_use_cases.py \
  backend/tests/unit/test_meeting_evaluation.py -v
```

### Tiêu chí Đạt (Pass Criteria):
- 100% test cases đều pass (xanh).
- Test case kiểm tra hành vi mặc định `target_date is None` xác nhận rằng use case tự động trừ lùi đúng 2 ngày (`today - timedelta(days=2)`).
- Test case kiểm tra hành vi truyền `target_date` cụ thể xác nhận rằng use case sử dụng chính xác ngày được truyền vào (không bị trừ lùi tiếp).
- Test case `CheckEvaluationDeadlineJobUseCase` xác nhận rằng:
  - Buổi học kết thúc <= 72h trước: KHÔNG tạo vi phạm.
  - Buổi học kết thúc > 72h trước: Tạo vi phạm với thông điệp "trong vòng 72h".

---

## 3. Chạy Thử nghiệm Thủ công (Manual Dry-Run via Trigger Script)

Kiểm tra script chạy tác vụ nền `trigger_jobs.py`:

```bash
# 1. Chạy với target_date = today (hệ thống kiểm tra ngày hôm nay):
PYTHONPATH=backend backend/.venv/bin/python -m app.scripts.trigger_jobs

# 2. Chạy với ngày cụ thể trong quá khứ:
PYTHONPATH=backend backend/.venv/bin/python -m app.scripts.trigger_jobs --date 2026-10-29
```

---

## 4. Tóm tắt Kiểm thử Nghiệm thu (Acceptance Checklist)

- [ ] **Homework**: Chạy job ngày $T+2$ phạt bài tập hạn ngày $T$. Chạy job ngày $T$ không phạt bài tập hạn $T$.
- [ ] **Meeting Attendance**: Chạy job ngày $T+2$ phạt vắng/trễ họp ngày $T$. Chạy job ngày $T$ không phạt họp ngày $T$.
- [ ] **Duty**: Chạy job ngày $T+2$ phạt ca trực ngày $T$. Chạy job ngày $T$ không phạt ca trực ngày $T$.
- [ ] **Meeting Evaluation**: Buổi học kết thúc cách đây 48 tiếng chưa bị phạt; kết thúc cách đây 73 tiếng bị phạt với lý do "trong vòng 72h".
