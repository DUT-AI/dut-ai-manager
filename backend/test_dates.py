from datetime import datetime

now = datetime(2026, 4, 8, 5, 0, 0)
homework_deadline = datetime(2026, 4, 7, 23, 59, 0)
req_start_time = datetime(2026, 4, 11, 23, 59, 0)

if now <= homework_deadline:
    print("Skipped by deadline")
else:
    print("Passed deadline check")

if now <= req_start_time:
    print("Skipped by postpone")
else:
    print("Passed postpone check. VIOLATION!")
