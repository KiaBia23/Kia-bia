from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# تابع برای فرمان start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام')

def main():
    # توکن ربات خود را وارد کنید
    BOT_TOKEN = '8179916091:AAGTvIX32x5dGBtgwdllsEpbYzOO1vbL9Y4'
    
    # ایجاد اپدیت کننده و دیسپچر
    updater = Updater(BOT_TOKEN)

    # اضافه کردن فرمان
    updater.dispatcher.add_handler(CommandHandler("start", start))

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
