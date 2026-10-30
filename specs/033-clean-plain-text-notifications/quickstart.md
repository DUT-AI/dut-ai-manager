# Quickstart & Verification Guide

## Mục tiêu kiểm thử
Xác nhận rằng:
1. Tất cả các thông báo tạo ra không còn chứa ký tự Markdown thô (`**`, `*`, `` ` ``, `[]()`).
2. Định dạng thông báo đọc rõ ràng, đẹp mắt trên Zalo Bot, Discord Embed, In-App Modal.
3. Không làm gãy bất kỳ bài kiểm thử unit tests nào hiện có.

## Kiểm tra nhanh

### 1. Chạy Unit Test Backend
```bash
uv run --directory backend pytest tests/unit/
```
Kỳ vọng: 161/161 unit tests pass.

### 2. Kiểm tra tĩnh không còn chuỗi Markdown thô trong các file notification
```bash
python3 -c "
import os, re
files = [
    'backend/app/shared/infrastructure/notification/zalo_channel.py',
    'backend/app/homework/application/event_handlers.py',
    'backend/app/meeting/application/event_handlers.py',
    'backend/app/permission_request/application/event_handlers.py',
    'backend/app/duty/notification_handler.py',
    'backend/app/billing/application/notification_handler.py',
    'backend/app/bonus_point/notification_handler.py',
    'backend/app/violation/notification_handler.py',
    'backend/app/auth/account_notification_handler.py',
    'backend/app/reminder/application/reminder_dispatcher.py',
    'backend/app/reminder/application/embed_builder.py'
]
bad = []
for f in files:
    content = open(f).read()
    if '**' in content: bad.append((f, '**'))
    if re.search(r'\[.*\]\(.*\)', content): bad.append((f, 'link'))
assert len(bad) == 0, f'Vẫn còn markdown trong: {bad}'
print('All clean!')
"
```

### 3. Kiểm tra Build Frontend
```bash
npm --prefix frontend run build
```
Kỳ vọng: Vite build thành công không có lỗi TypeScript.
