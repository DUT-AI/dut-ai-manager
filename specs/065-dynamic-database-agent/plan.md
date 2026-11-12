# Implementation Plan: Dynamic Database Inspector & Read-Only SQL Agent

**Feature ID**: `065-dynamic-database-agent`  
**Branch**: `065-dynamic-database-agent`  
**Trạng thái**: In Planning  

---

## Technical Context

- **Backend**: FastAPI, Python 3.12, SQLAlchemy 2.0 (`sqlalchemy.inspect`), PostgreSQL / Psycopg.
- **Chatbot Module**: `backend/app/chatbot/`
  - Tool Registry: `ChatbotToolRegistry` (`backend/app/chatbot/infrastructure/tools/registry.py`).
  - Tools Directory: `backend/app/chatbot/infrastructure/tools/database/`.
  - System Prompt: Cập nhật hướng dẫn cho Agent cách sử dụng 4 công cụ theo luồng Progressive Discovery trong `backend/app/chatbot/application/send_chat_message_use_case.py`.
- **Testing**: `backend/tests/unit/test_database_tools.py` và `test_chatbot.py`.

---

## Constitution Check

- [x] **I. Clean Architecture & DDD**: Toàn bộ logic kiểm tra schema và thực thi SQL an toàn nằm trong Infrastructure layer (`infrastructure/tools/database/`), kế thừa `BaseChatbotTool`.
- [x] **II. Dependency Injection with Dishka**: Session được inject thông qua `ChatbotToolRegistry` hiện tại.
- [x] **III. Enterprise UTC**: Mọi timestamp trả về từ SQL query được format chuẩn UTC / ISO / VN timezone.
- [x] **X. Security Armor & Zero Write Mutation**: Chặn 100% mọi thao tác ghi dữ liệu, chỉ cho phép `SELECT`. Tự động mask các cột mật khẩu và token.

---

## Phases & Milestones

### Phase 0: Research & Schemas (Hoàn tất)
- [x] Phân tích thiết kế Progressive Discovery 4 bước.
- [x] Xây dựng hợp đồng dữ liệu trong `specs/065-dynamic-database-agent/data-model.md`.

### Phase 1: Xây dựng Bộ 4 Công Cụ Database (Backend)
- [ ] Tạo thư mục `backend/app/chatbot/infrastructure/tools/database/`.
- [ ] Cài đặt `db_list_tables.py` (`DbListTablesTool`).
- [ ] Cài đặt `db_get_table_schema.py` (`DbGetTableSchemaTool`) kèm cơ chế lọc bỏ `SENSITIVE_COLUMNS`.
- [ ] Cài đặt `db_get_table_relationships.py` (`DbGetTableRelationshipsTool`) phân tích Foreign Keys và sinh `join_hint`.
- [ ] Cài đặt `db_execute_query.py` (`DbExecuteQueryTool`) kèm bộ lọc Read-Only AST/Regex, timeout 5s và Auto `LIMIT 50`.
- [ ] Đăng ký 4 tools vào `ChatbotToolRegistry` (`registry.py`).

### Phase 2: Cập Nhật Prompt Hướng Dẫn Cho Agent
- [ ] Bổ sung hướng dẫn vào `SYSTEM_PROMPT` trong `send_chat_message_use_case.py`:
  - Khuyến khích Agent sử dụng quy trình: `db_list_tables` $\rightarrow$ `db_get_table_relationships` / `db_get_table_schema` $\rightarrow$ `db_execute_query` khi người dùng hỏi các câu hỏi đối soát phức tạp hoặc thông tin chi tiết của một thành viên cụ thể.

### Phase 3: Unit Testing & Verification
- [ ] Viết unit tests kiểm thử kiểm soát bảo mật: Chặn câu lệnh `DROP TABLE`, `DELETE`, `UPDATE`.
- [ ] Viết unit tests kiểm thử việc tự động mask cột mật khẩu.
- [ ] Viết unit test mô phỏng Agent Loop chạy thực tế: Tìm kiếm vi phạm của "Nguyễn Lê Vy" qua query động.
