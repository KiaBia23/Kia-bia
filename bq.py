from telethon import TelegramClient, events
import ccxt
import sqlite3
import re
import asyncio

# تنظیمات اتصال تلگرام
API_ID = 13303149
API_HASH = 'f76c4ae86376dd73cabfab262ef7115d'
SESSION_NAME = 'kai'

# تنظیمات کوینکس
COINEX_API_KEY = '6570135D34654FE9B0A135704815AD3E'
COINEX_SECRET_KEY = 'BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E'

# شناسه کانال سیگنال
SIGNAL_CHANNEL_ID = 'testtestrre'

# ایجاد کلاینت تلگرام
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# تنظیم اکسچنج کوینکس
exchange = ccxt.coinex({
    'apiKey': COINEX_API_KEY,
    'secret': COINEX_SECRET_KEY,
    'enableRateLimit': True
})

# تنظیم دیتابیس
conn = sqlite3.connect('trading_signals.db')
cursor = conn.cursor()

# ایجاد جدول تنظیمات کاربر
cursor.execute('''
CREATE TABLE IF NOT EXISTS trading_settings (
    user_id INTEGER PRIMARY KEY,
    amount REAL,
    coin TEXT
)
''')

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


@client.on(events.NewMessage(pattern='/balance'))
async def balance_handler(event):
    """نمایش موجودی کاربر در کوینکس"""
    try:
        balance = exchange.fetch_balance()
        total_balance = sum(amount for amount in balance['total'].values() if amount > 0)
        free_balance = sum(amount for amount in balance['free'].values() if amount > 0)

        response = f"""📊 **موجودی حساب کوینکس**  
💰 **موجودی کل:** {total_balance:.4f} USDT  
🔹 **موجودی در دسترس:** {free_balance:.4f} USDT"""

        await event.reply(response)
    except Exception as e:
        await event.reply(f"❌ خطا در دریافت موجودی: {str(e)}")


@client.on(events.NewMessage(pattern='/set amount'))
async def set_amount(event):
    """تنظیم مقدار ترید توسط کاربر"""
    try:
        match = re.match(r'/set amount (\d+(\.\d+)?)\s*(\w+)', event.text)
        if not match:
            await event.reply("⚠️ فرمت نادرست. مثال: `/set amount 1 USDT`")
            return

        amount = float(match.group(1))
        coin = match.group(3).upper()

        cursor.execute('REPLACE INTO trading_settings (user_id, amount, coin) VALUES (?, ?, ?)', 
                       (event.sender_id, amount, coin))
        conn.commit()

        await event.reply(f"✅ مقدار {amount} {coin} با موفقیت تنظیم شد.")
    except Exception as e:
        await event.reply(f"❌ خطا: {str(e)}")


@client.on(events.NewMessage(pattern='/unset'))
async def unset_amount(event):
    """حذف تنظیمات کاربر"""
    try:
        cursor.execute('DELETE FROM trading_settings WHERE user_id = ?', (event.sender_id,))
        conn.commit()

        await event.reply("✅ تنظیمات معاملاتی شما حذف شد.")
    except Exception as e:
        await event.reply(f"❌ خطا: {str(e)}")


@client.on(events.NewMessage(chats=SIGNAL_CHANNEL_ID))
async def signal_channel_handler(event):
    """پردازش سیگنال‌های دریافتی از کانال"""
    try:
        pattern = r'Coin\s*#(\w+/USDT)\s*\n\s*Position:\s*(LONG|SHORT)\s*\n\s*Leverage:\s*Cross(\d+)X\s*\n\s*Entries:\s*([\d.-]+)\s*-\s*([\d.-]+)\s*\n\s*Targets:\s*🎯\s*([\d.,\s]+)\s*\n\s*Stop Loss:\s*([\d.-]+)'
        match = re.search(pattern, event.text, re.DOTALL)

        if match:
            coin_pair, position, leverage, entry_min, entry_max, targets_str, stop_loss = (
                match.group(1), match.group(2), int(match.group(3)), 
                float(match.group(4)), float(match.group(5)), 
                [float(t) for t in match.group(6).replace(' ', '').split(',')], 
                float(match.group(7))
            )

            cursor.execute('SELECT amount, coin FROM trading_settings WHERE user_id = ?', (event.sender_id,))
            user_settings = cursor.fetchone()

            if user_settings:
                trade_amount, trade_coin = user_settings

                # ذخیره سیگنال
                cursor.execute('''
                INSERT INTO active_signals (user_id, coin_pair, position, leverage, entry_min, entry_max, targets, stop_loss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event.sender_id, coin_pair, position, leverage, entry_min, entry_max, targets_str, stop_loss))
                conn.commit()

                # ارسال پیام سیگنال
                signal_msg = f"""🚨 **سیگنال جدید دریافت شد**  
📈 **جفت ارز:** {coin_pair}  
📊 **موقعیت:** {position}  
🎯 **تارگت‌ها:** {', '.join(map(str, targets))}  
💹 **محدوده ورود:** {entry_min} - {entry_max}  
🛑 **استاپ لاس:** {stop_loss}"""
                
                await client.send_message(event.sender_id, signal_msg)

                # شروع بررسی قیمت
                asyncio.create_task(monitor_signal(event.sender_id, coin_pair, entry_min, entry_max, targets, stop_loss, trade_amount, trade_coin))

    except Exception as e:
        print(f"❌ خطا در پردازش سیگنال: {str(e)}")


async def monitor_signal(user_id, coin_pair, entry_min, entry_max, targets, stop_loss, trade_amount, trade_coin):
    """بررسی تغییرات قیمت و اجرای معامله در صورت لزوم"""
    try:
        while True:
            current_price = exchange.fetch_ticker(coin_pair)['last']

            if entry_min <= current_price <= entry_max:
                # اجرای معامله
                side = 'buy' if 'LONG' in coin_pair else 'sell'
                try:
                    exchange.create_market_order(symbol=coin_pair, type='market', side=side, amount=trade_amount)
                    
                    trade_report = f"""✅ **معامله انجام شد**  
📈 **جفت ارز:** {coin_pair}  
💰 **قیمت ورود:** {current_price}  
🎯 **هدف اول:** {targets[0]}  
🛑 **استاپ لاس:** {stop_loss}"""
                    
                    await client.send_message(user_id, trade_report)
                    break

                except Exception as trade_error:
                    await client.send_message(user_id, f"❌ خطا در اجرای معامله: {str(trade_error)}")
                    break

            await asyncio.sleep(30)

    except Exception as e:
        print(f"❌ خطا در مانیتورینگ سیگنال: {str(e)}")


async def main():
    await client.start()
    print("✅ ربات با موفقیت راه‌اندازی شد.")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
