from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# تابع برای فرمان start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('سلام')

def main():
    # توکن ربات خود را وارد کنید
    BOT_TOKEN = '8179916091:AAGTvIX32x5dGBtgwdllsEpbYzOO1vbL9Y4'
    
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()

    # اضافه کردن فرمان
    application.add_handler(CommandHandler("start", start))

    # شروع ربات
    application.run_polling()

if __name__ == '__main__':
    main()
