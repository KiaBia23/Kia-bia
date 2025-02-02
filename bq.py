import cloudscraper
import json
import logging
from telethon import TelegramClient, events

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# اطلاعات تلگرام
API_ID = 13303149
API_HASH = 'f76c4ae86376dd73cabfab262ef7115d'
SESSION_NAME = 'kia'
TARGET_GROUP_USERNAME = '@kiakirt'

# اطلاعات API مقصد
API_URL = "https://bcgame.li/api/activity/redeemCode/useCode/"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# ایجاد اسکرپر برای دور زدن Cloudflare
scraper = cloudscraper.create_scraper()

# اتصال به تلگرام
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def send_api_request(message):
    data = {"redeemCode": message}
    try:
        response = scraper.post(API_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ درخواست موفق: %s", result)
            return json.dumps(result, indent=4)
        else:
            logger.error("❌ خطا در API: %s", response.text)
            return response.text
    except Exception as e:
        logger.error(f"🚨 خطا در ارسال درخواست API: {e}")
        return str(e)

@client.on(events.NewMessage(chats=TARGET_GROUP_USERNAME))
async def handle_new_message(event):
    try:
        message = event.raw_text.strip()
        logger.info(f"📩 پیام جدید دریافت شد: {message}")
        result = await send_api_request(message)
        await event.reply(f"🔹 پاسخ API:\n{result}")
    except Exception as e:
        logger.error(f"⚠️ خطا: {e}")
        await event.reply(f"❌ خطا در پردازش پیام: {e}")

async def main():
    logger.info("🚀 بات در حال اجرا است...")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
  
