# Quickstart Validation: Chuyển hoàn toàn Deadline sang Assignees (039-per-assignee-homework-deadline)

Tài liệu này hướng dẫn chạy các kịch bản kiểm thử tự động và xác thực sau khi xóa bỏ cột `deadline` ở bảng `homeworks` và chuyển hẳn sang `homework_assignees`.

---

## Kịch bản 1: Migration DB & Backfill dữ liệu
1. Chạy migration:
   - Cột `deadline` được tạo trên `homework_assignees` và backfill từ `homeworks.deadline`.
   - Cột `deadline` bị xoá khỏi `homeworks`.
2. **Kỳ vọng**:
   - `SELECT column_name FROM information_schema.columns WHERE table_name='homeworks' AND column_name='deadline';` -> Rỗng (0 rows).
   - `SELECT count(*) FROM homework_assignees WHERE deadline IS NULL;` -> 0 rows.

---

## Kịch bản 2: Tạo bài tập mới và lưu Deadline cho Assignees
1. Admin tạo bài tập "Lesson 1" với deadline `2026-11-10 23:59:59 UTC`, phân công User 10 và User 20.
2. **Kỳ vọng**:
   - Bảng `homeworks` tạo bản ghi bài tập (không có cột `deadline`).
   - Bảng `homework_assignees` tạo 2 bản ghi:
     - User 10: `deadline = 2026-11-10 23:59:59 UTC`.
     - User 20: `deadline = 2026-11-10 23:59:59 UTC`.

---

## Kịch bản 3: User 20 xin hoãn bài tập (`POSTPONE`)
1. User 20 nộp đơn xin hoãn bài tập đến `2026-11-14 23:59:59 UTC`.
2. **Kỳ vọng**:
   - `PostponeStrategy.on_created` lưu `old_deadline = 2026-11-10 23:59:59 UTC` vào payload đơn.
   - Bản ghi của User 20 trong `homework_assignees` được cập nhật: `deadline = 2026-11-14 23:59:59 UTC`.
   - Bản ghi của User 10 trong `homework_assignees` giữ nguyên `2026-11-10 23:59:59 UTC`.

---

## Kịch bản 4: Quét vi phạm độc lập (Job chạy ngày 2026-11-12, target_date = 2026-11-10)
1. Cả User 10 và User 20 đều chưa nộp bài.
2. Job chạy kiểm tra ngày `2026-11-10`:
3. **Kỳ vọng**:
   - Chỉ có User 10 có `assignee.deadline` vào ngày `2026-11-10` -> User 10 bị ghi nhận vi phạm quá hạn.
   - User 20 có `assignee.deadline = 2026-11-14` -> Hoàn toàn KHÔNG bị quét vi phạm trong ngày 12!

---

## Kịch bản 5: Quét vi phạm khi hết hạn gia hạn (Job chạy ngày 2026-11-16, target_date = 2026-11-14)
1. Đến ngày `2026-11-14`, User 20 vẫn chưa nộp bài.
2. Vào ngày `2026-11-16` (sau 2 ngày), job quét ngày `2026-11-14`:
3. **Kỳ vọng**:
   - User 20 xuất hiện trong danh sách `due_assignments` của ngày `2026-11-14`.
   - User 20 bị tạo vi phạm quá hạn chuẩn xác, không bị lọt vi phạm!

---

## Kịch bản 6: User 20 huỷ đơn xin hoãn
1. User 20 xoá đơn xin hoãn đã nộp.
2. **Kỳ vọng**:
   - `PostponeStrategy.on_deleted` hoàn nguyên `assignee.deadline` của User 20 về `payload.old_deadline` (`2026-11-10 23:59:59 UTC`).
