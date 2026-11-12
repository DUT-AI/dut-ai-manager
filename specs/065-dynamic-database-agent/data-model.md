# Data Contracts & Schemas: Dynamic Database Explorer Tools

**Feature ID**: `065-dynamic-database-agent`  
**Ngày cập nhật**: 2026-11-12  

---

## 1. Tool 1: `db_list_tables`

### Tool Definition
```json
{
  "name": "db_list_tables",
  "description": "Liệt kê danh sách tất cả các bảng trong cơ sở dữ liệu kèm mô tả nghiệp vụ ngắn gọn để xác định bảng cần tra cứu.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### Response Schema
```json
{
  "total_tables": 12,
  "tables": [
    {"name": "users", "description": "Thông tin thành viên CLB/Lab (họ tên, email, số điện thoại, trạng thái)"},
    {"name": "violations", "description": "Lịch sử biên bản vi phạm (ngày vi phạm, lý do phạt, user_id)"},
    {"name": "meetings", "description": "Lịch trình các buổi sinh hoạt/học tập định kỳ"},
    {"name": "meeting_participants", "description": "Điểm danh và trạng thái tham gia buổi học của thành viên"},
    {"name": "homeworks", "description": "Danh sách các bài tập được giao"},
    {"name": "homework_assignees", "description": "Hạn nộp và phân công bài tập cho từng thành viên"},
    {"name": "homework_submissions", "description": "Lịch sử nộp bài, điểm số và trạng thái chấm bài"}
  ]
}
```

---

## 2. Tool 2: `db_get_table_schema`

### Tool Definition
```json
{
  "name": "db_get_table_schema",
  "description": "Lấy thông tin chi tiết về các cột, kiểu dữ liệu và khóa chính của một bảng cụ thể.",
  "parameters": {
    "type": "object",
    "properties": {
      "table_name": {
        "type": "string",
        "description": "Tên bảng cần xem chi tiết (ví dụ: 'users', 'violations', 'meetings')."
      }
    },
    "required": ["table_name"]
  }
}
```

### Response Schema
```json
{
  "table_name": "violations",
  "primary_key": ["id"],
  "columns": [
    {"name": "id", "type": "INTEGER", "nullable": false},
    {"name": "user_id", "type": "INTEGER", "nullable": false},
    {"name": "reason", "type": "VARCHAR(255)", "nullable": false},
    {"name": "date", "type": "TIMESTAMP WITH TIME ZONE", "nullable": false},
    {"name": "is_deleted", "type": "BOOLEAN", "nullable": false}
  ]
}
```

---

## 3. Tool 3: `db_get_table_relationships`

### Tool Definition
```json
{
  "name": "db_get_table_relationships",
  "description": "Xem mối quan hệ khóa ngoại (Foreign Keys) giữa các bảng để biết cách viết câu lệnh JOIN chính xác.",
  "parameters": {
    "type": "object",
    "properties": {
      "tables": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Danh sách các bảng cần kiểm tra liên kết (ví dụ: ['users', 'violations'])."
      }
    },
    "required": ["tables"]
  }
}
```

### Response Schema
```json
{
  "target_tables": ["users", "violations"],
  "relationships": [
    {
      "source_table": "violations",
      "source_column": "user_id",
      "target_table": "users",
      "target_column": "id",
      "join_hint": "JOIN users ON users.id = violations.user_id"
    }
  ]
}
```

---

## 4. Tool 4: `db_execute_query`

### Tool Definition
```json
{
  "name": "db_execute_query",
  "description": "Thực thi câu lệnh SQL SELECT an toàn trên database PostgreSQL và trả về danh sách kết quả JSON.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Câu lệnh SQL bắt đầu bằng SELECT hoặc WITH (tuyệt đối không dùng INSERT/UPDATE/DELETE)."
      }
    },
    "required": ["query"]
  }
}
```

### Response Schema
```json
{
  "row_count": 2,
  "columns": ["id", "name", "date", "reason"],
  "rows": [
    {"id": 1, "name": "Nguyễn Lê Vy", "date": "07/11/2026 23:59", "reason": "Vắng sinh hoạt định kỳ"},
    {"id": 2, "name": "Nguyễn Lê Vy", "date": "03/11/2026 23:59", "reason": "Chưa hoàn thành bài tập coding"}
  ]
}
```
