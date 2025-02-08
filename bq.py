import telebot

# توکن ربات خود را اینجا قرار دهید
TOKEN = "7080490948:AAFG2V89znK3q5XLM3XD5vjKBtONJSITDww"

# ایجاد نمونه ربات
bot = telebot.TeleBot(TOKEN)

# تعریف دستور start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! به ربات ما خوش اومدی! 👋")

# اجرای ربات
print("ربات در حال اجراست...")
bot.infinity_polling()
