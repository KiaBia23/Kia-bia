import ccxt

# اطلاعات کوینکس
COINEX_ACCESS_ID = "6570135D34654FE9B0A135704815AD3E"
COINEX_SECRET_KEY = "BB419487C1EC71040BDD3464609EE63B0EEDA4A40A74D74E"

# راه‌اندازی کلاینت کوینکس
exchange = ccxt.coinex({
    'apiKey': COINEX_ACCESS_ID,
    'secret': COINEX_SECRET_KEY,
    'enableRateLimit': True
})

try:
    # تست دریافت اطلاعات بازار
    markets = exchange.fetch_markets()
    print("✅ اتصال به کوینکس برقرار است!")

    # تست دریافت موجودی حساب
    balance = exchange.fetch_balance()
    print("✅ دریافت موجودی موفقیت‌آمیز بود!")
    print(balance)  # نمایش موجودی‌ها

except ccxt.AuthenticationError:
    print("❌ خطای احراز هویت! API Key یا Secret اشتباه است یا دسترسی کافی ندارد.")
except ccxt.NetworkError:
    print("🌐 خطای شبکه! اینترنت یا سرور کوینکس بررسی شود.")
except Exception as e:
    print(f"⚠️ خطای دیگر: {str(e)}")
