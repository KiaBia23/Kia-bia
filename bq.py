import ccxt
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# اطلاعات کوینکس
COINEX_ACCESS_ID = "BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E"
COINEX_SECRET_KEY = "6570135D34654FE9B0A135704815AD3E"

# اطلاعات ربات تلگرام
BOT_TOKEN = "7080490948:AAFG2V89znK3q5XLM3XD5vjKBtONJSITDww"

# راه‌اندازی کلاینت کوینکس
exchange = ccxt.coinex({
    'apiKey': COINEX_ACCESS_ID,
    'secret': COINEX_SECRET_KEY,
    'options': {'defaultType': 'spot'}
})

# دستور /start برای نمایش اطلاعات حساب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        balance = exchange.fetch_balance()  # دریافت موجودی حساب
        total_balance = sum(balance['total'].values())  # محاسبه کل دارایی
        message = f"💰 اطلاعات حساب کوینکس شما:\n\n"
        message += f"📊 کل دارایی: {total_balance:.4f} USD\n\n"

        # نمایش دارایی‌های غیر صفر
        for asset, amount in balance['total'].items():
            if amount > 0:
                message += f"🔹 {asset}: {amount:.4f}\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت اطلاعات: {str(e)}")

# راه‌اندازی ربات
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 ربات در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
