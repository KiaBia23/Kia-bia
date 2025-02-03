from telethon import TelegramClient, events
from telethon.tl.types import MessageEntitySpoiler
import re

# اطلاعات برای اتصال
api_id = 13303149
api_hash = 'f76c4ae86376dd73cabfab262ef7115d'
session_name = 'kia'

# اتصال به تلگرام
client = TelegramClient(session_name, api_id, api_hash)

# لیست‌ها و تنظیمات
group_list = [-1001633920381]  # لیست آیدی گروه‌ها
user_list = [7593564011, 679559213, 1406920647, 2056833482, 722062998, 1915005327, 6260129627, 5351915758, 6930838046, 6736891021, 625886849, 6445249107, 7118547020, 6575250790, 8000636096, 7845948946, 7529894756, 7682933346, 7024851600]  # لیست آیدی کاربران
target_group = -1002382541592  # آیدی گروه هدف
source_channel = 'bcgamenotificacoes'  # کانال منبع
target_group_alias = '@kiakirt'  # گروه هدف دیگر

# تابع برای استخراج متن‌های خاص از پیام
def extract_texts(message):
    texts = []
    # استخراج متن‌هایی که دقیقا بین $ قرار دارند
    texts += re.findall(r'\$.*?\$', message)
    
    # استخراج متن‌های اسپویلر
    spoilers = re.findall(r'\|\|(.*?)\|\|', message)
    for spoiler in spoilers:
        # استخراج $text$ ها داخل اسپویلر
        spoiler_texts = re.findall(r'\$.*?\$', spoiler)
        if spoiler_texts:
            texts += spoiler_texts
        else:
            texts.append(spoiler)
    
    return texts

# مدیریت پیام‌های گروه
@client.on(events.NewMessage(chats=group_list))
async def handle_group_message(event):
    # چک کردن اینکه فرستنده در لیست کاربران است
    if event.sender_id in user_list:
        texts = extract_texts(event.raw_text)
        for text in texts:
            await client.send_message(target_group, text)

# مدیریت پیام‌های کانال
@client.on(events.NewMessage(chats=source_channel))
async def handle_channel_message(event):
    message = event.message
    
    # بررسی وجود اسپویلر در پیام
    if any(isinstance(entity, MessageEntitySpoiler) for entity in message.entities or []):
        spoiler_text = ""
        
        # استخراج متن اسپویلر
        for entity in message.entities:
            if isinstance(entity, MessageEntitySpoiler):
                spoiler_text += message.raw_text[entity.offset:entity.offset + entity.length] + "\n"
        
        # ارسال متن اسپویلر به گروه هدف
        if spoiler_text:
            await client.send_message(target_group_alias, spoiler_text)

# شروع کلاینت با مدیریت سشن
async def main():
    print("ربات فعال است...")
    # اگر سشن موجود نیست، شماره تلفن و کد تأییدیه را درخواست می‌کند
    await client.start()
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
