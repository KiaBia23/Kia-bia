from telethon import TelegramClient, events
import ccxt
import re
import sqlite3
import asyncio

# تنظیمات اتصال به تلگرام
API_ID = '7184795'
API_HASH = '06827b8819cf02361c2513c498ac645c'
SESSION_NAME = 'kai'

# تنظیمات کوینکس
COINEX_API_KEY = '6570135D34654FE9B0A135704815AD3E'
COINEX_SECRET_KEY = 'BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E'

# شناسه کانال سیگنال
SIGNAL_CHANNEL_ID = -100246711740  

# ایجاد کلاینت تلگرام
client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)

# تنظیم اکسچنج کوینکس
exchange = ccxt.coinex({
    'apiKey': COINEX_API_KEY,
    'secret': COINEX_SECRET_KEY,
    'enableRateLimit': True
})

# تنظیم دیتابیس
conn = sqlite3.connect('trading_signals.db')
cursor = conn.cursor()

# ایجاد جدول سیگنال‌ها
cursor.execute('''
CREATE TABLE IF NOT EXISTS active_signals (
    user_id INTEGER,
    coin_pair TEXT,
    position TEXT,
    leverage INTEGER,
    entry_min REAL,
    entry_max REAL,
    targets TEXT,
    stop_loss REAL,
    status TEXT DEFAULT 'PENDING'
)
''')
conn.commit()

async def monitor_signal_targets(user_id, coin_pair, position, leverage, entry_min, entry_max, targets, stop_loss):
    """ بررسی مداوم قیمت برای ورود به معامله """
    try:
        while True:
            # دریافت قیمت لحظه‌ای
            try:
                current_price = exchange.fetch_ticker(coin_pair)['last']
            except Exception as e:
                await client.send_message(user_id, f"❌ خطا در دریافت قیمت: {str(e)}")
                await asyncio.sleep(30)
                continue

            # بررسی ورود به محدوده قیمتی
            if entry_min <= current_price <= entry_max:
                try:
                    # اجرای معامله
                    order = execute_trade(coin_pair, position, leverage, current_price, targets, stop_loss)
                    trade_report = f"""✅ **معامله انجام شد**:
📌 جفت ارز: {coin_pair}
📉 موقعیت: {position}
💰 قیمت ورود: {current_price}
🎯 تارگت اول: {targets[0]}
🛑 استاپ لاس: {stop_loss}"""
                    await client.send_message(user_id, trade_report)
                    break  # بعد از اجرا، مانیتورینگ را متوقف کن
                except Exception as trade_error:
                    await client.send_message(user_id, f"❌ خطا در انجام معامله: {str(trade_error)}")
                    break

            # پیام انتظار
            await asyncio.sleep(30)  # بررسی هر ۳۰ ثانیه
    except Exception as e:
        print(f"⚠️ خطا در مانیتورینگ سیگنال: {str(e)}")

def execute_trade(coin_pair, position, leverage, entry_price, targets, stop_loss):
    """ اجرای معامله در کوینکس """
    try:
        side = 'buy' if position == 'LONG' else 'sell'
        order = exchange.create_market_order(
            symbol=coin_pair,
            type='market',
            side=side,
            amount=10,  # مقدار ثابت برای تست، می‌توان مقدار واقعی را جایگذاری کرد
            params={
                'leverage': leverage,
                'stopLoss': stop_loss,
                'takeProfit': targets[0]
            }
        )
        return order
    except Exception as e:
        raise Exception(f"⚠️ خطا در اجرای معامله: {str(e)}")

@client.on(events.NewMessage(chats=SIGNAL_CHANNEL_ID))
async def signal_channel_handler(event):
    """ پردازش پیام‌های سیگنال از کانال تلگرام """
    try:
        signal_pattern = r'Coin\s*#(\w+/USDT)\s*\n\s*Position:\s*(LONG|SHORT)\s*\n\s*Leverage:\s*Cross(\d+)X\s*\n\s*Entries:\s*([\d.-]+)\s*-\s*([\d.-]+)\s*\n\s*Targets:\s*🎯\s*([\d.,\s]+)\s*\n\s*Stop Loss:\s*([\d.-]+)'
        match = re.search(signal_pattern, event.text, re.DOTALL)

        if match:
            coin_pair = match.group(1)
            position = match.group(2)
            leverage = int(match.group(3))
            entry_min = float(match.group(4))
            entry_max = float(match.group(5))
            targets_str = match.group(6).replace(' ', '')
            targets = [float(target) for target in targets_str.split(',')]
            stop_loss = float(match.group(7))

            # ذخیره سیگنال در دیتابیس
            cursor.execute('''
                INSERT INTO active_signals 
                (user_id, coin_pair, position, leverage, entry_min, entry_max, targets, stop_loss) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event.sender_id, coin_pair, position, leverage, entry_min, entry_max, targets_str, stop_loss))
            conn.commit()

            # ارسال اطلاعات اولیه به کاربر
            signal_report = f"""🚨 **سیگنال جدید دریافت شد**:
📈 جفت ارز: {coin_pair}
🔼 موقعیت: {position}
💹 اهرم: {leverage}X
🎯 محدوده ورود: {entry_min} - {entry_max}
🎳 تارگت‌ها: {targets_str}
🛑 استاپ لاس: {stop_loss}"""

            await client.send_message(event.sender_id, signal_report)

            # شروع مانیتورینگ قیمت
            asyncio.create_task(monitor_signal_targets(event.sender_id, coin_pair, position, leverage, entry_min, entry_max, targets, stop_loss))

    except Exception as e:
        print(f"⚠️ خطا در پردازش سیگنال: {str(e)}")

# راه‌اندازی کلاینت
async def main():
    await client.start()
    print("✅ ربات با موفقیت اجرا شد.")
    await client.run_until_disconnected()

# اجرای اصلی
with client:
    client.loop.run_until_complete(main())
        
