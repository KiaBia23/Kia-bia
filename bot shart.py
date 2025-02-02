import telebot
from telebot import types
import os
import json
import time
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# تنظیمات ریترای و تایم‌اوت
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# تنظیمات اصلی ربات
telebot.apihelper.SESSION = http
telebot.apihelper.READ_TIMEOUT = 30
telebot.apihelper.CONNECT_TIMEOUT = 30

bot = telebot.TeleBot("7679901840:AAEpybJnayKF2SPEVwK-CofGfRTcATdCFz4")
CHANNEL_ID = "@kiakiree"
CHANNEL_LINK = "https://t.me/kiakiree"

# تنظیمات ترون
TRON_PRO_API_KEY = "0775a6a6-3ba3-48fa-845e-3bc32ff57376"
WALLET_FILE = "wallets.json"

# تنظیم اتصال به شبکه ترون با API Key
provider = HTTPProvider(
    endpoint_uri='https://api.trongrid.io',
    api_key=TRON_PRO_API_KEY,
    timeout=30
)
client = Tron(provider=provider)

# سیستم کش برای موجودی
balance_cache = {}

# سیستم وضعیت کاربران
user_status = defaultdict(lambda: {"accepted_rules": False})

# بارگذاری یا ایجاد فایل ولت‌ها
if os.path.exists(WALLET_FILE):
    with open(WALLET_FILE, 'r', encoding='utf-8') as f:
        wallets = json.load(f)
else:
    wallets = {}

def create_tron_wallet():
    """ایجاد ولت ترون جدید"""
    try:
        priv_key = PrivateKey.random()
        address = priv_key.public_key.to_base58check_address()
        return address, priv_key.hex()
    except Exception as e:
        print(f"Error creating wallet: {e}")
        return None, None

def get_tron_balance(address):
    """دریافت موجودی ترون با سیستم کش"""
    current_time = time.time()
    
    # چک کردن کش
    if address in balance_cache:
        last_check, balance = balance_cache[address]
        if current_time - last_check < 300:  # 5 دقیقه
            return balance
    
    try:
        balance = client.get_account_balance(address)
        balance_cache[address] = (current_time, float(balance))
        return float(balance)
    except Exception as e:
        print(f"Error getting balance: {e}")
        return balance_cache.get(address, (0, 0))[1]

def check_membership(user_id):
    """بررسی سریع عضویت کاربر"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def create_join_keyboard():
    """کیبورد عضویت در کانال"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    join_button = types.InlineKeyboardButton(
        "🌟 عضویت در کانال", 
        url=CHANNEL_LINK
    )
    check_button = types.InlineKeyboardButton(
        "✅ بررسی عضویت", 
        callback_data="check_join"
    )
    markup.add(join_button, check_button)
    return markup

def create_main_menu_keyboard():
    """کیبورد منوی اصلی"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    profile_button = types.KeyboardButton("👤 حساب کاربری")
    support_button = types.KeyboardButton("🛠 پشتیبانی")
    game_button = types.KeyboardButton("🎮 شروع بازی")
    rules_button = types.KeyboardButton("📜 قوانین")
    markup.add(profile_button, support_button, game_button, rules_button)
    return markup

def create_profile_menu_keyboard():
    """کیبورد حساب کاربری"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    deposit_button = types.KeyboardButton("💰 شارژ")
    withdraw_button = types.KeyboardButton("💸 برداشت")
    back_button = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(deposit_button, withdraw_button, back_button)
    return markup

def create_deposit_menu_keyboard():
    """کیبورد شارژ"""
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    tron_button = types.KeyboardButton("🚀 ترون")
    back_button = types.KeyboardButton("🔙 بازگشت")
    markup.add(tron_button, back_button)
    return markup

def show_profile(chat_id, user_id):
    """نمایش اطلاعات حساب کاربری"""
    try:
        if user_id not in wallets:
            address, recovery_code = create_tron_wallet()
            if address is None:
                bot.send_message(chat_id, "❌ خطا در ایجاد کیف پول. لطفا دوباره تلاش کنید.")
                return

            wallets[user_id] = {
                "address": address,
                "recovery_code": recovery_code,
                "balance": 0,
                "name": "کاربر جدید"
            }
            with open(WALLET_FILE, 'w', encoding='utf-8') as f:
                json.dump(wallets, f, ensure_ascii=False, indent=4)

        user_wallet = wallets[user_id]
        balance = get_tron_balance(user_wallet['address'])

        profile_text = f"""
👤 *اطلاعات حساب کاربری*

🆔 شناسه کاربری: `{user_id}`
👨‍💼 نام: {user_wallet.get('name', 'کاربر جدید')}
💰 موجودی: {balance} TRX

📋 آدرس کیف پول ترون:
`{user_wallet['address']}`

⚠️ لطفا آدرس و کد بازیابی خود را در جای امنی ذخیره کنید.
"""
        bot.send_message(
            chat_id,
            profile_text,
            reply_markup=create_profile_menu_keyboard(),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error in show_profile: {e}")
        bot.send_message(
            chat_id,
            "⚠️ متأسفانه در نمایش اطلاعات حساب مشکلی پیش آمده است. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_keyboard()
        )

def show_rules(chat_id):
    """نمایش قوانین با فرمت زیبا"""
    rules_text = """
📜 *قوانین استفاده از ربات*

1️⃣ رعایت ادب و احترام در استفاده از ربات

2️⃣ عدم ارسال محتوای نامناسب یا مغایر با قوانین

3️⃣ عدم سوء استفاده از امکانات ربات

4️⃣ رعایت حریم خصوصی سایر کاربران

5️⃣ پرهیز از ارسال پیام‌های مکرر و اسپم

⚠️ در صورت عدم رعایت قوانین، دسترسی شما محدود خواهد شد.

📌 لطفاً در صورت موافقت با قوانین، دکمه تایید را بزنید.
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    accept_button = types.InlineKeyboardButton("✅ قوانین را می‌پذیرم", callback_data="accept_rules")
    reject_button = types.InlineKeyboardButton("❌ نمی‌پذیرم", callback_data="reject_rules")
    markup.add(accept_button, reject_button)
    bot.send_message(chat_id, rules_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user = message.from_user
        user_id = user.id
        
        if check_membership(user_id):
            if user_status[user_id]["accepted_rules"]:
                bot.send_message(
                    message.chat.id,
                    "به منوی اصلی خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    reply_markup=create_main_menu_keyboard()
                )
            else:
                show_rules(message.chat.id)
        else:
            join_text = f"""
👋 سلام {user.first_name} عزیز

♦️ برای استفاده از ربات، لطفا ابتدا عضو کانال ما شوید.

⚡️ پس از عضویت، دکمه بررسی عضویت را بزنید.
"""
            bot.reply_to(
                message,
                join_text,
                reply_markup=create_join_keyboard()
            )
    except Exception as e:
        print(f"Error in start handler: {e}")

@bot.message_handler(func=lambda message: message.text == "👤 حساب کاربری")
def profile(message):
    """مدیریت حساب کاربری"""
    try:
        show_profile(message.chat.id, message.from_user.id)
    except Exception as e:
        print(f"Error in profile handler: {e}")

@bot.message_handler(func=lambda message: message.text == "💰 شارژ")
def deposit(message):
    """مدیریت شارژ کاربر"""
    try:
        bot.send_message(
            message.chat.id,
            "لطفاً روش شارژ خود را انتخاب کنید:",
            reply_markup=create_deposit_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in deposit handler: {e}")

@bot.message_handler(func=lambda message: message.text == "🚀 ترون")
def deposit_tron(message):
    """شارژ با ترون"""
    try:
        user_id = message.from_user.id
        if user_id in wallets:
            address = wallets[user_id]["address"]
            deposit_text = f"""
💎 *شارژ حساب با ترون*

📍 آدرس کیف پول شما:
`{address}`

⚠️ لطفا دقت کنید:
• فقط ترون (TRX) ارسال کنید
• حداقل مبلغ ارسالی 1 TRX است
• پس از ارسال، موجودی به صورت خودکار بروز می‌شود

🔄 برای بررسی موجودی به بخش حساب کاربری مراجعه کنید.
"""
            bot.send_message(
                message.chat.id,
                deposit_text,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ خطا: حساب کاربری یافت نشد.")
    except Exception as e:
        print(f"Error in deposit_tron handler: {e}")

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به منوی اصلی")
def back_to_main_menu(message):
    """بازگشت به منوی اصلی"""
    try:
        bot.send_message(
            message.chat.id,
            "به منوی اصلی بازگشتید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=create_main_menu_keyboard()
        )
    except Exception as e:
        print(f"Error in back_to_main_menu handler: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """مدیریت تمام کال‌بک‌ها"""
    try:
        user_id = call.from_user.id

        if call.data == "check_join":
            if check_membership(user_id):
                show_rules(call.message.chat.id)
            else:
                bot.answer_callback_query(
                    call.id,
                    "❌ شما هنوز عضو کانال نشده‌اید!",
                    show_alert=True
                )

        elif call.data == "accept_rules":
            user_status[user_id]["accepted_rules"] = True
            welcome_text = f"""
✨ {call.from_user.first_name} عزیز

✅ از پذیرش قوانین سپاسگزاریم
⭐️ اکنون می‌توانید از امکانات ربات استفاده کنید

🌟 موفق باشید
"""
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=welcome_text
            )
            bot.send_message(
                call.message.chat.id,
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=create_main_menu_keyboard()
            )
            bot.answer_callback_query(call.id, "✅ قوانین با موفقیت پذیرفته شد!")

        elif call.data == "reject_rules":
            reject_text = f"""
⚠️ {call.from_user.first_name} عزیز

❌ متأسفانه بدون پذیرش قوانین امکان استفاده از ربات وجود ندارد.

🔄 در صورت تغییر نظر می‌توانید مجدداً /start را ارسال کنید.
"""
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=reject_text
            )
            bot.answer_callback_query(call.id, "❌ قوانین رد شد!")
            
    except Exception as e:
        print(f"Error in callback handler: {e}")
        try:
            bot.answer_callback_query(
                call.id,
                "❌ متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
                show_alert=True
            )
        except:
            pass

def run_bot():
    """اجرای ربات با مدیریت خطا"""
    while True:
        try:
            print("✅ ربات با موفقیت شروع به کار کرد...")
            print(f"🤖 نام ربات: {bot.get_me().first_name}")
            print(f"🔗 لینک ربات: @{bot.get_me().username}")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ خطا در اجرای ربات: {e}")
            print("🔄 تلاش مجدد برای اتصال در 5 ثانیه...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    try:
        # ایجاد فایل‌های مورد نیاز
        if not os.path.exists(WALLET_FILE):
            with open(WALLET_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        
        print("🚀 در حال راه‌اندازی ربات...")
        run_bot()
    except KeyboardInterrupt:
        print("\n✋ ربات با موفقیت متوقف شد.")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
