# Feature Specification: Dynamic Database Inspector & Read-Only SQL Agent

**Feature ID**: `065-dynamic-database-agent`  
**Trạng thái**: Draft / In Planning  
**Ngày tạo**: 2026-11-12  

---

## 1. Giới thiệu & Động lực (Context & Motivation)

Hệ thống quản lý `dut-ai-manager` sở hữu nhiều miền dữ liệu phức tạp (Buổi học, Bài tập, Vi phạm, Đơn từ, Điểm thưởng, Thành viên...).
Hiện tại, AI Agent muốn tra cứu dữ liệu nào thì lập trình viên phải tự tay viết trước một công cụ (Tool) cụ thể tương ứng (ví dụ: `admin_get_meeting_absentees`, `admin_get_unsubmitted_homeworks`, `inspect_entity_records`...).

### Hạn chế lớn:
- **Kém linh hoạt**: Khi người dùng hỏi một câu hỏi đối soát chéo bất kỳ (ví dụ: *"Liệt kê danh sách chi tiết các vi phạm của Nguyễn Lê Vy"*, hoặc *"Thống kê số buổi vắng họp và số bài tập nộp trễ của từng thành viên trong tháng qua"*), AI không thể trả lời vì chưa có tool được code sẵn cho kịch bản đó.
- **Tốn công sức bảo trì**: Mỗi lần schema cơ sở dữ liệu thay đổi hoặc có bảng mới, lập trình viên lại phải định nghĩa và bảo trì thêm hàng chục tool mới.

### Giải pháp:
Trang bị cho AI Agent bộ công cụ **Dynamic Database Explorer (Text-to-SQL an toàn)** theo kiến trúc **Progressive Discovery (Khám phá lũy tiến)**:
Thay vì dồn toàn bộ DDL database vào prompt gây nghẽn context, AI sẽ khám phá từng bước:
1. `db_list_tables`: Xem danh sách và vai trò tổng quan của các bảng.
2. `db_get_table_schema`: Soi chi tiết cột, kiểu dữ liệu, khóa chính của bảng nó quan tâm.
3. `db_get_table_relationships`: Xem sơ đồ quan hệ / Foreign Keys giữa các bảng kèm `join_hint` để biết cách JOIN chuẩn xác.
4. `db_execute_query`: Thực thi câu lệnh `SELECT` an toàn tuyệt đối với bộ lọc phòng thủ (Strict Read-Only, Masking cột mật khẩu/token, Auto LIMIT 50).

---

## 2. Mục tiêu (Goals & Non-Goals)

### Mục tiêu chính (Goals):
1. **Khám phá lũy tiến (Progressive Discovery)**:
   - Tool `db_list_tables`: Danh sách bảng và mô tả nghiệp vụ ngắn gọn.
   - Tool `db_get_table_schema`: Cấu trúc chi tiết của 1 bảng (tự động ẩn các trường nhạy cảm như `hashed_password`, `token`, `secret`, `api_key`).
   - Tool `db_get_table_relationships`: Phân tích Foreign Keys giữa các bảng được chọn, trả về quan hệ trực tiếp và gợi ý cú pháp `JOIN`.
   - Tool `db_execute_query`: Chạy câu lệnh SQL `SELECT` an toàn.
2. **An toàn & Phòng thủ dữ liệu (Strict Security Guardrails)**:
   - **Chỉ đọc tuyệt đối (Read-Only)**: Chặn 100% các câu lệnh chứa `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `CREATE`, `EXEC`, v.v.
   - **Ràng buộc giới hạn bản ghi (Auto Limit)**: Tự động ép `LIMIT 50` nếu câu query không có hoặc có LIMIT vượt quá 100, ngăn ngừa nghẽn server.
   - **Bảo mật quyền hạn (RBAC)**: Chỉ cấp bộ công cụ này cho người dùng có quyền quản trị/đối soát (ví dụ Admin, Mentor, Trainer với các quyền READ tương ứng).
   - **Tự động thích ứng**: Tự động nhận diện bảng mới trong cơ sở dữ liệu mà không cần chỉnh sửa code.

### Ngoài phạm vi (Non-Goals):
- Không hỗ trợ thao tác ghi (`WRITE`, `MUTATION`) qua SQL động (các nghiệp vụ ghi như tạo buổi học, duyệt đơn... vẫn phải qua Domain Use Case truyền thống).
- Không mở quyền truy cập trực tiếp SQL cho thành viên thường (thành viên thường tiếp tục dùng các công cụ cá nhân an toàn).

---

## 3. Yêu cầu Người dùng & Kịch bản (User Scenarios & Requirements)

### Kịch bản 1: Tra cứu vi phạm chi tiết của một thành viên cụ thể (Nguyễn Lê Vy)
- **Actor**: Quản trị viên / Mentor / HR.
- **Hành động**: Đặt câu hỏi: *"Hãy liệt kê các lỗi vi phạm của Nguyễn Lê Vy"*.
- **Chu trình Agent Loop**:
  - Vòng 1: Agent gọi `db_list_tables` $\rightarrow$ Thấy bảng `users` và `violations`.
  - Vòng 2: Agent gọi `db_get_table_relationships(tables=['users', 'violations'])` $\rightarrow$ Nhận được gợi ý: `violations.user_id = users.id`.
  - Vòng 3: Agent gọi `db_execute_query` với câu lệnh:
    ```sql
    SELECT v.id, v.date, v.reason 
    FROM violations v 
    JOIN users u ON u.id = v.user_id 
    WHERE u.name ILIKE '%Nguyễn Lê Vy%' AND v.is_deleted = false 
    ORDER BY v.date DESC;
    ```
  - Vòng 4: Agent nhận 10 bản ghi và định dạng thành bảng Markdown chuyên nghiệp cho người dùng.

### Kịch bản 2: Truy vấn thống kê đối soát chéo nhiều bảng
- **Actor**: Ban Chủ nhiệm.
- **Hành động**: *"Cho anh biết top 5 thành viên vắng sinh hoạt nhiều nhất kèm số điện thoại và email để liên hệ"*.
- **Chu trình Agent Loop**:
  - Agent tự động liên kết `meeting_participants`, `meetings` và `users` qua các khóa ngoại, chạy query `GROUP BY` và trả về kết quả chính xác trong vài giây.
