import psycopg2
import os
from psycopg2 import sql

conn = psycopg2.connect(
    host="100.84.187.107",
    port=5444,
    user="postgres",
    password="postgres",
    dbname="dut_ai_manager_dev"
)
conn.autocommit = True
cur = conn.cursor()

commands = [
    "ALTER TABLE users ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE meeting_participants ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE homework_submissions ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE homeworks ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE permission_requests ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE invoices ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE permission_requests ALTER COLUMN category TYPE VARCHAR USING category::VARCHAR",
    "ALTER TABLE meetings ALTER COLUMN status TYPE VARCHAR USING status::VARCHAR",
    "ALTER TABLE meetings ALTER COLUMN capacity_status TYPE VARCHAR USING capacity_status::VARCHAR",
    
    "UPDATE users SET status = 'ACTIVE' WHERE status = 'đang hoạt động'",
    "UPDATE users SET status = 'INACTIVE' WHERE status = 'đã nghỉ'",
    
    "UPDATE meeting_participants SET status = 'NOT_JOINED' WHERE status = 'chưa tham gia'",
    "UPDATE meeting_participants SET status = 'JOINED' WHERE status = 'đã checkin'",
    "UPDATE meeting_participants SET status = 'COMPLETED' WHERE status = 'đã checkout'",
    
    "UPDATE homework_submissions SET status = 'NOT_SUBMITTED' WHERE status = 'chưa nộp'",
    "UPDATE homework_submissions SET status = 'SUBMITTED' WHERE status = 'đã nộp'",
    "UPDATE homework_submissions SET status = 'LEADER_CHECKED' WHERE status = 'nhóm trưởng đã duyệt'",
    "UPDATE homework_submissions SET status = 'FINISHED' WHERE status IN ('đã chấm điểm', 'đã duyệt')",
    
    "UPDATE homeworks SET status = 'OPEN' WHERE status IN ('đang diễn ra', 'đang mở')",
    "UPDATE homeworks SET status = 'CLOSED' WHERE status IN ('đã kết thúc', 'đã đóng')",
    
    "UPDATE permission_requests SET status = 'PENDING' WHERE status IN ('đang chờ', 'đang chờ duyệt')",
    "UPDATE permission_requests SET status = 'APPROVED' WHERE status IN ('đã chấp nhận', 'chấp nhận')",
    "UPDATE permission_requests SET status = 'REJECTED' WHERE status IN ('đã từ chối', 'từ chối')",
    "UPDATE permission_requests SET status = 'CANCELLED' WHERE status = 'đã hủy'",
    
    "UPDATE invoices SET status = 'PENDING' WHERE status = 'chưa thanh toán'",
    "UPDATE invoices SET status = 'PAID' WHERE status = 'đã thanh toán'",
    "UPDATE invoices SET status = 'CANCELLED' WHERE status = 'đã hủy'",
]

for cmd in commands:
    try:
        cur.execute(cmd)
        print(f"SUCCESS: {cmd}")
    except Exception as e:
        print(f"FAILED: {cmd} - {e}")

cur.close()
conn.close()
