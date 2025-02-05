import os
import ccxt
from telegram.ext import ApplicationBuilder, CommandHandler

TELEGRAM_TOKEN = os.getenv('7549969402:AAEYI_tYnOV79Z9G7cPkpCvCQUewHI9NosA')
COINEX_API_KEY = os.getenv('BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E')
COINEX_SECRET = os.getenv('6570135D34654FE9B0A135704815AD3E')

async def start(update, context):
    if not (COINEX_API_KEY and COINEX_SECRET):
        await update.message.reply_text('کلیدهای API یا Secret تنظیم نشده‌اند.')
        return
    try:
        exchange = ccxt.coinex({
            'apiKey': COINEX_API_KEY,
            'secret': COINEX_SECRET,
            'enableRateLimit': True
        })
        balance = exchange.fetch_balance()
        message = 'اطلاعات حساب شما:\n'
        for currency, data in balance.items():
            if isinstance(data, dict) and 'free' in data:
                message += f"{currency}: {data['free']}\n"
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت اطلاعات: {str(e)}")

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.run_polling()

if __name__ == '__main__':
    main()
