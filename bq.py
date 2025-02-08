from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# توکن ربات رو اینجا قرار بدید
TOKEN = "7080490948:AAFG2V89znK3q5XLM3XD5vjKBtONJSITDww"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """این تابع زمانی که کاربر /start را وارد میکند اجرا میشود"""
    
    # گرفتن نام کاربر
    user_name = update.message.from_user.first_name
    
    # ارسال پیام خوش‌آمدگویی
    welcome_message = f"سلام {user_name} عزیز! 😊\nبه ربات ما خوش اومدی!"
    await update.message.reply_text(welcome_message)

async def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    
    # ایجاد نمونه از برنامه
    application = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلر برای دستور /start
    application.add_handler(CommandHandler("start", start_command))
    
    # شروع پردازش پیام‌های ورودی
    print("ربات شروع به کار کرد...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
