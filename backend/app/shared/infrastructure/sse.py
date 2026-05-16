import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any


class SseBroadcaster:
    """
    Quản lý các kết nối SSE (subscribers) và phát tin nhắn tới tất cả mọi người.
    """

    def __init__(self):
        # Lưu trữ các queue của từng client đang lắng nghe
        self.subscribers: list[asyncio.Queue] = []

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Đăng ký một client mới và tạo queue cho client đó"""
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                try:
                    # Chờ đợi message từ queue với timeout để gửi heartbeat
                    # 30 giây là khoảng thời gian an toàn cho Cloudflare (thường ngắt ở 100s)
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    # Format dữ liệu theo chuẩn SSE: "data: <json>\n\n"
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                except TimeoutError:
                    # Gửi heartbeat (comment trong SSE bắt đầu bằng dấu :) để giữ kết nối
                    yield ": keep-alive\n\n"
        finally:
            # Cleanup: Xóa queue khi client ngắt kết nối
            if queue in self.subscribers:
                self.subscribers.remove(queue)

    async def broadcast(self, message: dict[str, Any]):
        """Gửi tin nhắn tới tất cả subscribers"""
        if not self.subscribers:
            return

        # Đẩy message vào tất cả các queue đang mở
        for queue in self.subscribers:
            await queue.put(message)


# Singleton instance để dùng chung toàn app
sse_broadcaster = SseBroadcaster()
