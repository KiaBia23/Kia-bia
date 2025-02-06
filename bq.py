from telethon import TelegramClient, events
import ccxt
import os
import re
import sqlite3
from dotenv import load_dotenv
import asyncio

# تنظیمات اتصال
API_ID = '7184795'
API_HASH = '06827b8819cf02361c2513c498ac645c'
SESSION_NAME = 'kai'

# تنظیمات کوینکس
COINEX_API_KEY = '6570135D34654FE9B0A135704815AD3E'
COINEX_SECRET_KEY = 'BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E'

# شناسه کانال سیگنال
SIGNAL_CHANNEL_ID = -1002467117400  

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

# ایجاد جدول‌ها
cursor.execute('''
CREATE TABLE IF NOT EXISTS trading_settings (
    user_id INTEGER PRIMARY KEY,
    amount REAL,
    coin TEXT
)
''')

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
    current_target_index INTEGER DEFAULT 0,
    entry_price REAL,
    status TEXT DEFAULT 'PENDING'
)
''')
conn.commit()

@client.on(events.NewMessage(pattern='/set amount'))
async def set_amount(event):
    try:
        match = re.match(r'/set amount (\d+(\.\d+)?)\s*(\w+)', event.text)
        if not match:
            await event.reply("فرمت نادرست. مثال: /set amount 1 usdt")
            return
        
        amount = float(match.group(1))
        coin = match.group(3).upper()
        
        cursor.execute('REPLACE INTO trading_settings (user_id, amount, coin) VALUES (?, ?, ?)', 
                       (event.sender_id, amount, coin))
        conn.commit()
        
        await event.reply(f"مقدار {amount} {coin} با موفقیت تنظیم شد.")
    
    except Exception as e:
        await event.reply(f"خطا: {str(e)}")

@client.on(events.NewMessage(pattern='/unset'))
async def unset_amount(event):
    try:
        cursor.execute('DELETE FROM trading_settings WHERE user_id = ?', (event.sender_id,))
        cursor.execute('DELETE FROM active_signals WHERE user_id = ?', (event.sender_id,))
        conn.commit()
        
        await event.reply("تنظیمات معاملاتی شما حذف شد.")
    
    except Exception as e:
        await event.reply(f"خطا: {str(e)}")

@client.on(events.NewMessage(pattern='/balance'))
async def balance_handler(event):
    try:
        balance = exchange.fetch_balance()
        total_balance = balance['total']
        free_balance = balance['free']
        
        response = "📊 موجودی حساب کوینکس\n\n"
        
        total_account_balance = sum(amount for amount in total_balance.values() if amount > 0)
        response += f"موجودی کل حساب: {total_account_balance:.4f} USDT\n\n"
        
        futures_balance = sum(amount for coin, amount in total_balance.items() if 'USDT' in coin and amount > 0)
        response += f"موجودی فیوچرز: {futures_balance:.4f} USDT\n\n"
        
        futures_free_balance = sum(amount for coin, amount in free_balance.items() if 'USDT' in coin and amount > 0)
        response += f"موجودی در دسترس فیوچرز: {futures_free_balance:.4f} USDT\n\n"
        
        spot_balance = sum(amount for coin, amount in total_balance.items() if 'USDT' not in coin and amount > 0)
        response += f"موجودی اسپات: {spot_balance:.4f} USDT"

        await event.reply(response)
    
    except Exception as e:
        await event.reply(f"خطا: {str(e)}")
async def monitor_signal_targets(user_id, coin_pair, position, leverage, 
                                  entry_min, entry_max, targets, stop_loss, 
                                  trade_amount, trade_coin):
    try:
        # اولین چک قیمت
        current_price = exchange.fetch_ticker(coin_pair)['last']
        
        # اگر قیمت در محدوده باشد (شامل خود اعداد محدوده)
        if entry_min <= current_price <= entry_max:
            try:
                # بررسی موجودی و اجرای معامله
                balance = exchange.fetch_balance()
                futures_coin_balance = balance['total'].get(trade_coin, 0)
                
                if futures_coin_balance < trade_amount:
                    trade_report = f"""❌ معامله انجام نشد:
🚫 دلیل: موجودی ناکافی
💰 موجودی فعلی: {futures_coin_balance:.4f} {trade_coin}
💸 مقدار مورد نیاز: {trade_amount} {trade_coin}"""
                    await client.send_message(user_id, trade_report)
                    return
                
                # اجرای معامله
                order = execute_trade(
                    coin_pair, position, leverage, 
                    current_price, targets, stop_loss, 
                    trade_amount, trade_coin
                )
                
                # محاسبه سود
                profit_percentage = ((targets[0] - current_price) / current_price) * leverage * 100
                profit_amount = trade_amount * (targets[0] - current_price)
                
                # گزارش معامله
                trade_report = f"""🎉 معامله با موفقیت اجرا شد:
📈 جفت ارز: {coin_pair}
💹 قیمت ورود: {current_price}
🎯 تارگت اول: {targets[0]}
📊 درصد سود پیش‌بینی: {profit_percentage:.2f}%
💰 مقدار سود پیش‌بینی: {profit_amount:.4f} USDT"""
                
                await client.send_message(user_id, trade_report)
                return
            
            except Exception as trade_error:
                error_report = f"""❌ معامله انجام نشد:
🚫 دلیل: {str(trade_error)}
📝 خطای سیستمی رخ داده است."""
                await client.send_message(user_id, error_report)
                return
        
        # اگر خارج از محدوده باشد، منتظر می‌ماند
        while True:
            current_price = exchange.fetch_ticker(coin_pair)['last']
            
            if entry_min <= current_price <= entry_max:
                # رسیدن به محدوده - اجرای معامله
                try:
                    balance = exchange.fetch_balance()
                    futures_coin_balance = balance['total'].get(trade_coin, 0)
                    
                    if futures_coin_balance < trade_amount:
                        trade_report = f"""❌ معامله انجام نشد:
🚫 دلیل: موجودی ناکافی
💰 موجودی فعلی: {futures_coin_balance:.4f} {trade_coin}
💸 مقدار مورد نیاز: {trade_amount} {trade_coin}"""
                        await client.send_message(user_id, trade_report)
                        break
                    
                    order = execute_trade(
                        coin_pair, position, leverage, 
                        current_price, targets, stop_loss, 
                        trade_amount, trade_coin
                    )
                    
                    profit_percentage = ((targets[0] - current_price) / current_price) * leverage * 100
                    profit_amount = trade_amount * (targets[0] - current_price)
                    
                    trade_report = f"""🎉 معامله با موفقیت اجرا شد:
📈 جفت ارز: {coin_pair}
💹 قیمت ورود: {current_price}
🎯 تارگت اول: {targets[0]}
📊 درصد سود پیش‌بینی: {profit_percentage:.2f}%
💰 مقدار سود پیش‌بینی: {profit_amount:.4f} USDT"""
                    
                    await client.send_message(user_id, trade_report)
                    break
                
                except Exception as trade_error:
                    error_report = f"""❌ معامله انجام نشد:
🚫 دلیل: {str(trade_error)}
📝 خطای سیستمی رخ داده است."""
                    await client.send_message(user_id, error_report)
                    break
            
            elif current_price < entry_min:
                report = f"""⏳ منتظر رسیدن قیمت به محدوده:
📈 قیمت فعلی: {current_price}
🎯 محدوده مورد نظر: {entry_min} - {entry_max}
🔹 وضعیت: در انتظار افزایش قیمت"""
                await client.send_message(user_id, report)
            
            elif current_price > entry_max:
                report = f"""⏳ منتظر رسیدن قیمت به محدوده:
📈 قیمت فعلی: {current_price}
🎯 محدوده مورد نظر: {entry_min} - {entry_max}
🔹 وضعیت: در انتظار کاهش قیمت"""
                await client.send_message(user_id, report)
            
            await asyncio.sleep(30)
    
    except Exception as e:
        print(f"خطا در مانیتورینگ سیگنال: {str(e)}")

def execute_trade(coin_pair, position, leverage, 
                  entry_price, targets, stop_loss, 
                  trade_amount, trade_coin):
    try:
        side = 'buy' if position == 'LONG' else 'sell'
        
        order = exchange.create_market_order(
            symbol=coin_pair,
            type='market',
            side=side,
            amount=trade_amount,
            params={
                'leverage': leverage,
                'stopLoss': stop_loss,
                'takeProfit': targets[0]
            }
        )
        
        return order
    
    except Exception as e:
        raise Exception(f"خطا در اجرای معامله: {str(e)}")

@client.on(events.NewMessage(chats=SIGNAL_CHANNEL_ID))
async def signal_channel_handler(event):
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
            
            cursor.execute('SELECT amount, coin FROM trading_settings')
            user_settings = cursor.fetchone()
            
            if user_settings:
                trade_amount, trade_coin = user_settings
                
                cursor.execute('''
                INSERT INTO active_signals 
                (user_id, coin_pair, position, leverage, entry_min, entry_max, targets, stop_loss) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event.sender_id, coin_pair, position, leverage, 
                      entry_min, entry_max, targets_str, stop_loss))
                conn.commit()
                
                raw_signal_report = f"""🚨 سیگنال جدید:
📈 جفت ارز: {coin_pair}
🔼 موقعیت: {position}
💹 اهرم: {leverage}X
🎯 محدوده ورود: {entry_min} - {entry_max}
🎳 تارگت‌ها: {targets_str}
🛑 استاپ لاس: {stop_loss}"""
                
                await client.send_message(event.sender_id, raw_signal_report)
                
                asyncio.create_task(monitor_signal_targets(
                    event.sender_id, coin_pair, position, leverage, 
                    entry_min, entry_max, targets, stop_loss, 
                    trade_amount, trade_coin
                ))
    
    except Exception as e:
        print(f"خطا در پردازش سیگنال کانال: {str(e)}")

# راه‌اندازی کلاینت
async def main():
    await client.start()
    print("سلف بات با موفقیت راه‌اندازی شد.")
    await client.run_until_disconnected()

# اجرای اصلی
with client:
    client.loop.run_until_complete(main())
    
