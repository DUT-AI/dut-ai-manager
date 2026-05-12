import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List


class SseBroadcaster:
    """
    Quản lý các kết nối SSE (subscribers) và phát tin nhắn tới tất cả mọi người.
    """

    def __init__(self):
        # Lưu trữ các queue của từng client đang lắng nghe
        self.subscribers: List[asyncio.Queue] = []

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Đăng ký một client mới và tạo queue cho client đó"""
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                # Chờ đợi message từ queue
                message = await queue.get()
                # Format dữ liệu theo chuẩn SSE: "data: <json>\n\n"
                yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
        finally:
            # Cleanup: Xóa queue khi client ngắt kết nối
            self.subscribers.remove(queue)

    async def broadcast(self, message: Dict[str, Any]):
        """Gửi tin nhắn tới tất cả subscribers"""
        if not self.subscribers:
            return

        # Đẩy message vào tất cả các queue đang mở
        for queue in self.subscribers:
            await queue.put(message)


# Singleton instance để dùng chung toàn app
sse_broadcaster = SseBroadcaster()
