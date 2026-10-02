"""
Script kiểm thử gửi thông báo trực tiếp đến Discord (DM hoặc Channel) với Rich Embed và Meme Images.

Cách sử dụng:
1. Gửi trực tiếp đến Discord User ID (DM):
   uv run python app/scripts/test_discord_notification.py --discord-id <DISCORD_USER_ID> --scenario all

2. Gửi thử một kịch bản cụ thể:
   uv run python app/scripts/test_discord_notification.py --discord-id <DISCORD_USER_ID> --scenario billing_invoice

3. Gửi thông qua User ID trong Database:
   uv run python app/scripts/test_discord_notification.py --user-id 1 --scenario homework_assigned

4. Gửi vào Discord Channel / Room (cho admin/quản lý):
   uv run python app/scripts/test_discord_notification.py --channel-id <DISCORD_CHANNEL_ID> --scenario permission_request
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Thêm thư mục backend vào sys.path
backend_path = Path(__file__).resolve().parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.shared.infrastructure.asset_helper import get_asset_url
from app.shared.infrastructure.database import engine
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.shared.infrastructure.notification_service import NotificationService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


def build_test_payloads(user_id: int = 1) -> dict[str, NotificationPayload]:
    """Tạo các payload mẫu tương ứng với các use case trong hệ thống."""
    frontend_url = settings.FRONTEND_HOST.rstrip("/")
    return {
        "billing_invoice": NotificationPayload(
            user_id=user_id,
            title="🧾 Thông báo hóa đơn định kỳ Tháng 10/2026",
            content="Bạn có hóa đơn định kỳ mới cần thanh toán với tổng số tiền 150,000 VND. Vui lòng thanh toán trước ngày 15/10/2026.",
            category=NotificationCategory.BILLING,
            level=NotificationLevel.INFO,
            image_asset="meme-xin-tien.jpeg",
            fields=[
                {"name": "Số tiền", "value": "150,000 VND", "inline": True},
                {"name": "Hạn chót", "value": "15/10/2026", "inline": True},
                {"name": "Mã hóa đơn", "value": "#INV-202610-001", "inline": False},
            ],
            action_url=f"{frontend_url}/dashboard/invoices",
        ),
        "billing_paid": NotificationPayload(
            user_id=user_id,
            title="✅ Thanh toán hóa đơn thành công",
            content="Hóa đơn #INV-202610-001 của bạn đã được xác nhận thanh toán thành công qua SePay.",
            category=NotificationCategory.BILLING,
            level=NotificationLevel.SUCCESS,
            image_asset="meme-lam-viec-3.jpeg",
            fields=[
                {"name": "Số tiền đã trả", "value": "150,000 VND", "inline": True},
                {"name": "Trạng thái", "value": "PAID", "inline": True},
            ],
            action_url=f"{frontend_url}/dashboard/invoices",
        ),
        "homework_assigned": NotificationPayload(
            user_id=user_id,
            title="📚 Bài tập mới: Xây dựng RAG Pipeline",
            content="Mentor vừa giao bài tập mới cho bạn với hạn nộp vào 23:59 ngày 08/10/2026.",
            category=NotificationCategory.HOMEWORK,
            level=NotificationLevel.INFO,
            image_asset="meme-hoc-bai.webp",
            fields=[
                {"name": "Chủ đề", "value": "AI Engineering", "inline": True},
                {"name": "Deadline", "value": "08/10/2026 23:59", "inline": True},
            ],
            action_url=f"{frontend_url}/dashboard/my-homeworks",
        ),
        "homework_graded": NotificationPayload(
            user_id=user_id,
            title="🎯 Điểm bài tập: Xây dựng RAG Pipeline",
            content="Mentor đã chấm bài tập của bạn: 9.5/10 (Xuất sắc!).",
            category=NotificationCategory.HOMEWORK,
            level=NotificationLevel.SUCCESS,
            image_asset="meme-lam-viec.webp",
            fields=[
                {"name": "Điểm số", "value": "9.5 / 10", "inline": True},
                {
                    "name": "Nhận xét",
                    "value": "Code clean, kiến trúc rất tốt!",
                    "inline": False,
                },
            ],
            action_url=f"{frontend_url}/dashboard/my-homeworks",
        ),
        "violation": NotificationPayload(
            user_id=user_id,
            title="⚠️ Cảnh báo vi phạm nội quy",
            content="Bạn bị ghi nhận vi phạm: Vắng mặt buổi sinh hoạt không phép (-20,000 VND).",
            category=NotificationCategory.VIOLATION,
            level=NotificationLevel.WARNING,
            image_asset="meme-khoc.webp",
            fields=[
                {"name": "Loại vi phạm", "value": "Vắng không phép", "inline": True},
                {"name": "Tiền phạt", "value": "20,000 VND", "inline": True},
            ],
            action_url=f"{frontend_url}/dashboard/violations",
        ),
        "bonus_point": NotificationPayload(
            user_id=user_id,
            title="⭐ Bạn nhận được điểm thưởng",
            content="Chúc mừng bạn đã hoàn thành xuất sắc thử thách nghiên cứu tuần này (+50 điểm).",
            category=NotificationCategory.BONUS_POINT,
            level=NotificationLevel.SUCCESS,
            image_asset="meme-ngac-nhien.jpeg",
            fields=[
                {"name": "Điểm cộng", "value": "+50 Điểm", "inline": True},
                {"name": "Lý do", "value": "Top 1 Benchmark Hackathon", "inline": True},
            ],
        ),
        "meeting": NotificationPayload(
            user_id=user_id,
            title="📅 Nhắc nhở: Buổi họp Weekly Team AI",
            content="Buổi sinh hoạt định kỳ sẽ diễn ra lúc 19:30 tối nay tại Phòng Lab E302 / Discord Voice.",
            category=NotificationCategory.MEETING,
            level=NotificationLevel.INFO,
            image_asset="anh-nhac-em-meme-9.webp",
            fields=[
                {"name": "Thời gian", "value": "19:30 - 21:00", "inline": True},
                {"name": "Địa điểm", "value": "Room E302 / Discord", "inline": True},
            ],
            action_url=f"{frontend_url}/dashboard/meetings",
        ),
        "permission_request": NotificationPayload(
            user_id=user_id,
            title="🔔 Yêu cầu xin phép mới cần duyệt",
            content="Thành viên Nguyễn Văn A đã gửi đơn xin vắng buổi sinh hoạt tuần này.",
            category=NotificationCategory.PERMISSION_REQUEST,
            level=NotificationLevel.WARNING,
            image_asset="meme-met-moi-lam-viec.jpg",
            fields=[
                {"name": "Người gửi", "value": "Nguyễn Văn A", "inline": True},
                {"name": "Lý do", "value": "Trùng lịch thi học phần", "inline": True},
            ],
            action_url=f"{frontend_url}/dashboard/permissions",
        ),
    }


async def main():
    parser = argparse.ArgumentParser(
        description="Test gửi thông báo Discord với Rich Embed và Meme"
    )
    parser.add_argument(
        "--discord-id", type=str, help="Discord User ID người nhận (gửi DM trực tiếp)"
    )
    parser.add_argument(
        "--channel-id", type=str, help="Discord Channel ID (gửi vào kênh/room)"
    )
    parser.add_argument(
        "--user-id",
        type=int,
        help="User ID trong DB hệ thống (gửi qua NotificationService)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        choices=[
            "all",
            "billing_invoice",
            "billing_paid",
            "homework_assigned",
            "homework_graded",
            "violation",
            "bonus_point",
            "meeting",
            "permission_request",
        ],
        help="Kịch bản cần test (mặc định: all)",
    )
    args = parser.parse_args()

    if not args.discord_id and not args.channel_id and not args.user_id:
        print(
            "❌ Lỗi: Bạn cần cung cấp ít nhất một trong các tham số: --discord-id, --channel-id hoặc --user-id"
        )
        print("\nVí dụ:")
        print(
            "  uv run python backend/app/scripts/test_discord_notification.py --discord-id 123456789012345678"
        )
        print(
            "  uv run python backend/app/scripts/test_discord_notification.py --discord-id 123456789012345678 --scenario billing_invoice"
        )
        sys.exit(1)

    print("==================================================")
    print("🚀 DUT-AI Manager - Discord Notification Test Tool")
    print(
        f"🔗 Bot Token Configured: {'✅ Yes' if settings.DISCORD_BOT_TOKEN else '❌ Missing'}"
    )
    print(f"🔗 Backend Public URL: {settings.BACKEND_PUBLIC_URL}")
    print("==================================================\n")

    discord_service = DiscordService()
    scenarios = build_test_payloads()

    selected_scenarios = (
        scenarios.items()
        if args.scenario == "all"
        else [(args.scenario, scenarios[args.scenario])]
    )

    # 1. Gửi qua User ID DB
    if args.user_id:
        with Session(engine) as db:
            user_repo = UserRepository(db)
            zalo_bot = ZaloBotClient()
            notification_service = NotificationService(
                discord_service=discord_service,
                zalo_bot=zalo_bot,
                user_repo=user_repo,
            )
            print(
                f"👤 Gửi thông báo cho User ID: {args.user_id} qua NotificationService..."
            )
            for name, payload in selected_scenarios:
                payload.user_id = args.user_id
                print(f"  ➡️ Đang gửi kịch bản: [{name}] - '{payload.title}'...")
                res = await notification_service.send_to_user(payload)
                print(f"     Kết quả: {res}")
                await asyncio.sleep(1)
        print("\n🎉 Hoàn thành kiểm thử qua User ID!")
        return

    # 2. Gửi trực tiếp qua Discord User ID (DM)
    if args.discord_id:
        print(f"💬 Gửi trực tiếp DM tới Discord ID: {args.discord_id}...")
        dummy_repo = UserRepository(None)  # type: ignore
        dummy_zalo = ZaloBotClient()
        notification_service = NotificationService(
            discord_service=discord_service,
            zalo_bot=dummy_zalo,
            user_repo=dummy_repo,
        )

        for name, payload in selected_scenarios:
            print(f"  ➡️ Đang gửi kịch bản: [{name}] - '{payload.title}'...")
            asset_url = (
                get_asset_url(payload.image_asset) if payload.image_asset else None
            )
            print(f"     📸 Image Asset: {payload.image_asset} -> {asset_url}")
            success = await notification_service._send_discord_with_retry(
                args.discord_id, payload
            )
            if success:
                print(f"     ✅ Gửi thành công: [{name}]")
            else:
                print(f"     ❌ Gửi thất bại: [{name}]")
            await asyncio.sleep(1.5)

        print("\n🎉 Hoàn thành kiểm thử DM Discord!")
        return

    # 3. Gửi vào Discord Channel ID (Room)
    if args.channel_id:
        print(f"📢 Gửi tới Discord Channel ID: {args.channel_id}...")
        dummy_repo = UserRepository(None)  # type: ignore
        dummy_zalo = ZaloBotClient()
        notification_service = NotificationService(
            discord_service=discord_service,
            zalo_bot=dummy_zalo,
            user_repo=dummy_repo,
        )

        for name, payload in selected_scenarios:
            print(f"  ➡️ Đang gửi kịch bản: [{name}] - '{payload.title}'...")
            success = await notification_service._send_discord_room_with_retry(
                args.channel_id, payload
            )
            if success:
                print(f"     ✅ Gửi thành công: [{name}]")
            else:
                print(f"     ❌ Gửi thất bại: [{name}]")
            await asyncio.sleep(1.5)

        print("\n🎉 Hoàn thành kiểm thử Channel Discord!")


if __name__ == "__main__":
    asyncio.run(main())
