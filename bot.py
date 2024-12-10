import requests
import time
import json
from datetime import datetime
import hmac
import hashlib

# إعداد التيلجرام
TELEGRAM_BOT_TOKEN = '7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBmM'
TELEGRAM_CHAT_ID = '-1001664466794'

# إعداد API Binance
BINANCE_API_KEY = "yoFhD26cK6bYZRdCXpMKYgOYZbFcrnpwpbgPlclWyE1tduYm4idjy2CTmVm8XdZf"
BINANCE_SECRET_KEY = "obKeJjUmJiRtzzCa0IkVAyEQ05m97xz0h5914WT4DsJeiyfIXvq3M7vTHoZ95DKq"
BASE_URL = "https://api.binance.com"

# قائمة العملات (70 عملة)
SYMBOLS = [
    'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT',
    'CELRUSDT', 'TRXUSDT', 'AVAXUSDT', 'ATOMUSDT', 'LINKUSDT', 'LTCUSDT',
    'ALGOUSDT', 'NEARUSDT', 'QNTUSDT', 'VETUSDT', 'FILUSDT', 'FLOWUSDT',
    'ICPUSDT', 'EGLDUSDT', 'XTZUSDT', 'MANAUSDT', 'SANDUSDT', 'FTMUSDT',
    'AXSUSDT', 'GALAUSDT', 'ONEUSDT', 'XECUSDT', 'CHZUSDT', 'ZILUSDT',
    'ROSEUSDT', 'BATUSDT'
]

# تتبع الإشارات المفتوحة
open_positions = {}

# إرسال الرسائل إلى التيلجرام
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# جلب بيانات الشموع
def fetch_candles(symbol, timeframe="15m", limit=5):
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": timeframe, "limit": limit}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return [{"timestamp": candle[0], "high": float(candle[2]), "close": float(candle[4]), "open": float(candle[1])} for candle in response.json()]
    except Exception as e:
        print(f"Error fetching candles for {symbol}: {e}")
        return []

# التحقق من الزخم وكسر القمة
def is_strong_momentum(candles):
    green_count = 0
    for candle in candles[-4:-1]:  # آخر 3 شموع
        if candle["close"] > candle["open"]:
            green_count += 1
    return green_count >= 3

# تنفيذ أمر الشراء
def place_market_buy_order(symbol, usd_amount):
    price = get_current_price(symbol)
    if price is None:
        return None
    quantity = round(usd_amount / price, 6)
    url = f"{BASE_URL}/api/v3/order"
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    try:
        response = requests.post(url, params=params, headers=headers)
        response.raise_for_status()
        send_telegram_message(f"✅ Market buy order placed for {symbol} with {usd_amount} USD at price {price}")
        return response.json()
    except Exception as e:
        print(f"Error placing buy order for {symbol}: {e}")
        return None

# تنفيذ أمر البيع بحد
def place_limit_sell_order(symbol, quantity, target_price):
    url = f"{BASE_URL}/api/v3/order"
    params = {
        "symbol": symbol,
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": f"{target_price:.6f}",
        "timestamp": int(time.time() * 1000)
    }
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    try:
        response = requests.post(url, params=params, headers=headers)
        response.raise_for_status()
        send_telegram_message(f"✅ Limit sell order placed for {symbol} at price {target_price}")
        return response.json()
    except Exception as e:
        print(f"Error placing sell order for {symbol}: {e}")
        return None

# جلب السعر الحالي
def get_current_price(symbol):
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {"symbol": symbol}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return float(response.json()["price"])
    except Exception as e:
        print(f"Error fetching current price for {symbol}: {e}")
        return None

# الوظيفة الرئيسية
def main():
    usd_amount = 100
    max_positions = 7
    while True:
        total_open_positions = len(open_positions)
        if total_open_positions >= max_positions:
            time.sleep(10)
            continue

        for symbol in SYMBOLS:
            if symbol in open_positions:
                continue

            candles = fetch_candles(symbol)
            if len(candles) < 5:
                continue

            previous_high = candles[-2]["high"]
            last_close = candles[-1]["close"]

            if last_close > previous_high and is_strong_momentum(candles):
                buy_order = place_market_buy_order(symbol, usd_amount)
                if buy_order:
                    buy_price = float(buy_order['fills'][0]['price'])
                    quantity = float(buy_order['executedQty'])
                    target_price = round(buy_price * 1.007, 6)
                    place_limit_sell_order(symbol, quantity, target_price)
                    open_positions[symbol] = {"quantity": quantity, "target_price": target_price}
        time.sleep(5)

if __name__ == "__main__":
    main()
