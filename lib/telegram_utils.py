# 📍 lib/telegram_utils.py
import os
from telegram import Bot, InlineKeyboardMarkup
from dotenv import load_dotenv
import logging
import httpx
import json

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN)

logger = logging.getLogger(__name__)
TELEGRAM_TOKEN = BOT_TOKEN


async def notify_user(user_id: int, message: str):
    try:
        await bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"❌ Gagal kirim ke user {user_id}: {e}")


async def notify_admin(message: str):
    try:
        await bot.send_message(chat_id=int(ADMIN_ID), text=message)
    except Exception as e:
        print(f"❌ Gagal kirim ke admin: {e}")


async def send_telegram_message(chat_id: int, text: str, parse_mode: str = None, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode  # bisa None atau "Markdown"/"MarkdownV2"/"HTML"
        }

        if reply_markup:
            if isinstance(reply_markup, InlineKeyboardMarkup):
                # convert InlineKeyboardMarkup ke dict JSON
                payload["reply_markup"] = json.loads(reply_markup.to_json())
            else:
                payload["reply_markup"] = reply_markup  # fallback kalau sudah dict

        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)
    except Exception as e:
        logger.exception(f"❌ Gagal mengirim pesan Telegram ke {chat_id}")
