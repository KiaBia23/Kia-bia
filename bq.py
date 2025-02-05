import os
from telegram.ext import Application, CommandHandler
import ccxt
import asyncio

# تنظیم توکن‌ها
TELEGRAM_TOKEN = "7549969402:AAEYI_tYnOV79Z9G7cPkpCvCQUewHI9NosA"
COINEX_API_KEY = "BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E"
COINEX_SECRET = "6570135D34654FE9B0A135704815AD3E"

# تابع نمایش اطلاعات حساب
async def start(update, context):
    try:
        # اتصال به کوینکس
        exchange = ccxt.coinex({
            'apiKey': COINEX_API_KEY,
            'secret': COINEX_SECRET,
            'enableRateLimit': True
        })
        
        # دریافت موجودی
        balance = exchange.fetch_balance()
        
        # ساخت پیام
        message = "💰 موجودی حساب شما:\n\n"
        
        # اضافه کردن ارزهایی که موجودی دارند
        for currency in balance['total']:
            if float(balance['total'][currency]) > 0:
                free = balance['free'][currency]
                used = balance['used'][currency]
                total = balance['total'][currency]
                
                message += f"🔸 {currency}:\n"
                message += f"  موجودی آزاد: {free}\n"
                message += f"  در حال استفاده: {used}\n"
                message += f"  کل: {total}\n\n"
        
        # دریافت اطلاعات حساب
        account_info = exchange.fetch_balance()['info']
        if 'username' in account_info:
            message += f"👤 نام کاربری: {account_info['username']}\n"
            
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت اطلاعات:\n{str(e)}")

async def main():
    # راه‌اندازی ربات
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # اضافه کردن هندلر دستور start/
    application.add_handler(CommandHandler("start", start))
    
    # شروع ربات
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
