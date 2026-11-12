# Research & Architecture Decisions: Dynamic Database Inspector & Progressive Discovery

**Feature ID**: `065-dynamic-database-agent`  
**Ngày nghiên cứu**: 2026-11-12  
**Tác giả**: Antigravity Orchestrator  

---

## 1. Nghiên cứu Kỹ thuật Khám phá Schema Lũy tiến (Progressive Discovery)

### Vấn đề của cách tiếp cận Dump Schema truyền thống:
- Hệ thống `dut-ai-manager` có hơn 20 bảng ORM (`users`, `roles`, `permissions`, `meetings`, `meeting_participants`, `meeting_evaluations`, `homeworks`, `homework_assignees`, `homework_submissions`, `violations`, `bonus_points`, `permission_requests`, `notifications`, `teams`...).
- Nếu chèn toàn bộ DDL hoặc Schema vào System Prompt:
  - Chiếm hàng nghìn tokens vô ích cho mỗi request.
  - Làm mô hình bị loãng sự chú ý (attention dilution), dễ sinh câu query sai bảng hoặc sai cột.
  - Mỗi khi thêm cột/bảng mới phải cập nhật thủ công prompt.

### Quyết định Kiến trúc: 4 Công cụ Phân tầng Tự động (Self-Reflecting Metadata)
Sử dụng trực tiếp `sqlalchemy.inspect(engine)` để đọc live metadata từ Database PostgreSQL:

1. **`db_list_tables`**:
   - Sử dụng `inspect(engine).get_table_names()`.
   - Kết hợp bảng từ điển mô tả ngắn (`TABLE_DESCRIPTIONS`) để AI hiểu ngữ cảnh nghiệp vụ của từng bảng.
   - Lọc bỏ các bảng kỹ thuật nội bộ (`alembic_version`, `celery_*`).
2. **`db_get_table_schema`**:
   - Sử dụng `inspect(engine).get_columns(table_name)`.
   - Trả về: `name`, `type` (VARCHAR, INTEGER, TIMESTAMPTZ, BOOLEAN...), `nullable`, `primary_key`.
   - **Bảo mật tuyệt đối**: Danh sách `SENSITIVE_COLUMNS = {"hashed_password", "token", "refresh_token", "api_key", "secret", "zalo_bind_code"}` bị lọc bỏ tự động, AI không bao giờ nhìn thấy hoặc truy vấn được.
3. **`db_get_table_relationships`**:
   - Sử dụng `inspect(engine).get_foreign_keys(table_name)`.
   - Hỗ trợ truyền 1 bảng hoặc danh sách nhiều bảng (ví dụ `["users", "violations"]`).
   - Tự động sinh `join_hint` chuẩn xác: `ON {table_a}.{col_a} = {table_b}.{col_b}` để LLM dùng trực tiếp vào mệnh đề `JOIN`.
4. **`db_execute_query`**:
   - Kiểm tra câu lệnh qua **SQL Guard AST / Regex Parser**:
     - Bắt buộc bắt đầu bằng `SELECT` hoặc `WITH`.
     - Cấm tuyệt đối: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `CREATE`, `REPLACE`, `EXEC`, `EXECUTE`, `CALL`.
     - Tự động kiểm tra và thêm `LIMIT 50` nếu chưa có.
     - Sử dụng execution timeout (ví dụ: `SET statement_timeout = 5000` - tối đa 5 giây) để chống câu lệnh đệ quy hoặc full table scan làm treo database.

---

## 2. Phòng thủ An Toàn & Bảo mật Dữ liệu (Security Guardrails)

| Nguy cơ | Biện pháp Phòng thủ |
| :--- | :--- |
| **SQL Injection gây phá hủy DB (DROP, DELETE)** | Bộ phân tích cú pháp chặn 100% mọi câu lệnh không phải `SELECT`. Chạy trên session read-only hoặc rollback ngay sau khi lấy kết quả. |
| **Lộ mật khẩu / API Key** | `db_get_table_schema` giấu tên cột nhạy cảm; `db_execute_query` kiểm tra Regex từ khóa nhạy cảm trong câu SELECT hoặc tự động mask giá trị trả về. |
| **Query quá tải (DoS / Treo server)** | Ép buộc `LIMIT 50` tối đa; áp dụng timeout 5 giây trên mỗi câu query. |
| **Thành viên thường lạm dụng đọc dữ liệu người khác** | Yêu cầu quyền RBAC: Chỉ mở cho tài khoản có quyền `ViolationPermission.READ` hoặc `RolePermission.READ` (Admin, Mentor, Trainer). |
