import requests
import json
import logging
import asyncio
from collections import deque
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, مثل Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Origin": "https://bcgame.li",
    "Referer": "https://bcgame.li/",
}
COOKIES = {
    "smidV2": "202412072313285599b6ae4023677dcc92d0055684d40a00e04053999714a90",
    "SESSION": "01anvhzsrvejpf1946ab4c60590d1fcfcf8d453f0e18b6cf53",
    "_ga": "GA1.1.1034880906.1733600619",
    "_ga_B23BPN2TGE": "GS1.1.1738079768.19.1.1738080079.0.0.0",
}

# ایجاد session برای درخواست‌های HTTP
session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)

# اتصال به تلگرام
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# صف برای ذخیره پیام‌ها
message_queue = deque()

def send_api_request(message):
    # اطمینان از کدگذاری صحیح برای ارسال داده‌ها
    data = {"redeemCode": message}
    try:
        # درخواست POST به API
        response = session.post(API_URL, json=data)
        
        # بررسی وضعیت پاسخ
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info("✅ درخواست موفق: %s", result)
                
                # 🔹 جلوگیری از خطای 'latin-1' و نمایش صحیح کاراکترهای فارسی و دیگر کاراکترهای خاص
                return json.dumps(result, indent=4, ensure_ascii=False)  
            except json.JSONDecodeError:
                logger.error("❌ پاسخ API نامعتبر (احتمالاً Cloudflare مانع شده است)")
                return "⚠️ پاسخ API نامعتبر است. احتمالاً Cloudflare درخواست را مسدود کرده است."
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
        message_queue.append((event, message))  # اضافه کردن پیام به صف

        # اگر هنوز در حال پردازش نیستیم، پردازش را آغاز کنیم
        if len(message_queue) == 1:
            await process_messages()

    except Exception as e:
        logger.error(f"⚠️ خطا: {e}")
        await event.reply(f"❌ خطا در پردازش پیام: {e}")

async def process_messages():
    while message_queue:
        event, message = message_queue.popleft()  # دریافت پیام از صف
        try:
            if not message:
                await event.reply("⚠️ پیام خالی است. لطفاً کد معتبر ارسال کنید.")
                continue

            result = send_api_request(message)
            await event.reply(f"🔹 پاسخ API:\n{result}")

        except Exception as e:
            logger.error(f"⚠️ خطا در پردازش پیام: {e}")
            await event.reply(f"❌ خطا در پردازش پیام: {e}")

async def main():
    while True:
        try:
            logger.info("🚀 بات در حال اجرا است...")
            await client.start()
            await client.run_until_disconnected()
        except Exception as e:
            logger.error(f"🔴 خطا در اتصال: {e}")
            logger.info("🕐 تلاش برای اتصال مجدد در 10 ثانیه...")
            await asyncio.sleep(10)

# اجرای برنامه
if __name__ == "__main__":
    asyncio.run(main())
    
