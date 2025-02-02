from telethon import TelegramClient, events
import aiohttp
import json
import asyncio
import logging
from collections import deque

# تنظیم لاگینگ برای ردیابی دقیق‌تر خطاها
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# اطلاعات اتصال به تلگرام
API_ID = 13303149
API_HASH = 'f76c4ae86376dd73cabfab262ef7115d'

# اطلاعات گروه هدف
TARGET_GROUP_USERNAME = '@kiakirt'

# اطلاعات API مقصد
API_URL = "https://bcgame.li/api/activity/redeemCode/useCode/"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Origin": "https://bcgame.li",
    "Referer": "https://bcgame.li/",
}
COOKIES = {
    "smidV2": "202412072313285599b6ae4023677dcc92d0055684d40a00e04053999714a90",
    "SESSION": "01anvhzsrvejpf1946ab4c60590d1fcfcf8d453f0e18b6cf53",
    "_ga": "GA1.1.1034880906.1733600619",
    "_ga_B23BPN2TGE": "GS1.1.1738079768.19.1.1738080079.0.0.0",
}

# صف برای ذخیره پیام‌ها
message_queue = deque()

async def send_api_request(message):
    """ارسال کد به API مقصد و دریافت پاسخ"""
    data = {"redeemCode": message}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=data, headers=HEADERS, cookies=COOKIES) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("درخواست با موفقیت ارسال شد: %s", result)
                    return json.dumps(result, indent=4)
                else:
                    error_text = await response.text()
                    logger.error("خطا در ارسال درخواست: %s", error_text)
                    return error_text
        except Exception as e:
            logger.error(f"خطا در ارسال درخواست API: {e}")
            return str(e)

@events.register(events.NewMessage(chats=TARGET_GROUP_USERNAME))
async def handle_new_message(event):
    """پردازش پیام‌های دریافتی از گروه هدف"""
    try:
        message = event.raw_text.strip()
        logger.info(f"پیام جدید دریافت شد: {message}")
        message_queue.append((event, message))  # اضافه کردن پیام به صف

        # اگر هنوز در حال پردازش نیستیم، پردازش را آغاز کنیم
        if len(message_queue) == 1:
            await process_messages()

    except Exception as e:
        logger.error(f"خطا: {e}")
        await event.reply(f"خطا در پردازش پیام: {e}")

async def process_messages():
    """پردازش پیام‌های صف به ترتیب"""
    while message_queue:
        event, message = message_queue.popleft()  # دریافت پیام از صف
        try:
            if not message:
                await event.reply("پیام خالی است. لطفاً کد معتبر ارسال کنید.")
                continue

            result = await send_api_request(message)
            await event.reply(f"پاسخ API:\n{result}")

        except Exception as e:
            logger.error(f"خطا در پردازش پیام: {e}")
            await event.reply(f"خطا در پردازش پیام: {e}")

async def main():
    """دریافت شماره، ورود به تلگرام و اجرای بات"""
    phone = input("شماره تلفن خود را وارد کنید (با کد کشور): ").strip()

    async with TelegramClient(phone, API_ID, API_HASH) as client:
        try:
            # بررسی اینکه آیا لاگین شده یا نه
            if not await client.is_user_authorized():
                print("در حال ارسال کد تأیید به تلگرام شما...")
                await client.send_code_request(phone)
                code = input("کد تأیید را وارد کنید: ").strip()
                await client.sign_in(phone, code)

            logger.info("بات در حال اجرا است...")
            client.add_event_handler(handle_new_message)  # ثبت هندلر برای پیام‌های جدید
            await client.run_until_disconnected()

        except Exception as e:
            logger.error(f"خطا در ورود: {e}")
            print("خطایی رخ داد. لطفاً بررسی کنید و دوباره اجرا کنید.")

# اجرای برنامه
if __name__ == "__main__":
    asyncio.run(main())
