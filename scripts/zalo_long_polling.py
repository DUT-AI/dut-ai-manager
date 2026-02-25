#!/usr/bin/env python3
import os
import sys
import httpx
from dotenv import load_dotenv
from zalo_bot import Update
from zalo_bot.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("ZALO_BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ LỖI: Không tìm thấy ZALO_BOT_TOKEN trong file .env!")
    sys.exit(1)

WEBHOOK_URL = "http://localhost:8001/api/v1/zalo-bot/webhook"


async def forward_to_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    sender_id = update.message.chat.id
    text = update.message.text
    print(f"[NHẬN TIN TỪ ZALO BOT] {sender_id}: {text}")

    webhook_payload = {
        "event_name": "user_send_text",
        "sender": {"id": str(sender_id)},
        "message": {"text": text},
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(WEBHOOK_URL, json=webhook_payload)
            if res.status_code == 200:
                print(f"✅ Đã Forward thành công ({res.status_code}): {text}")
            else:
                print(f"❌ Forward thất bại, Server Dev trả về: {res.status_code}")
        except Exception as e:
            print(f"❌ Lỗi gửi Webhook HTTPX: {e}")


if __name__ == "__main__":
    print("=========================================================")
    print("🚀 ĐANG CHẠY KỊCH BẢN ZALO BOT LONG-POLLING DÀNH CHO LOCAL")
    print(f"📡 Forwarding các tin nhắn tới Webhook: {WEBHOOK_URL}")
    print("=========================================================\n")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, forward_to_webhook))
    app.bot.delete_webhook()

    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng tool Long-polling.")
