import requests
import time
import json
from datetime import datetime

# إعداد التيلجرام
TELEGRAM_BOT_TOKEN = '7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBmM'
TELEGRAM_CHAT_ID = '-1001664466794'

# إعداد API Binance
BINANCE_API_KEY = 'yoFhD26cK6bYZRdCXpMKYgOYZbFcrnpwpbgPlclWyE1tduYm4idjy2CTmVm8XdZf'
BINANCE_SECRET_KEY = 'obKeJjUmJiRtzzCa0IkVAyEQ05m97xz0h5914WT4DsJeiyfIXvq3M7vTHoZ95DKq'
BASE_URL = "https://api.binance.com"

# قائمة العملات
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'SXPUSDT', 'SYSUSDT',
    'TOMOUSDT', 'TRXUSDT', 'TWTUSDT', 'VETUSDT', 'VGXUSDT', 'VITEUSDT', 'VTHOUSDT',
    'WAVESUSDT', 'XLMUSDT', 'XTZUSDT', 'ZECUSDT', 'ZILUSDT', 'ZRXUSDT', 'NEBLUSDT',
    'NEOUSDT', 'OGNUSDT', 'OMGUSDT', 'ONGUSDT', 'ONTUSDT', 'OXTUSDT', 'RSRUSDT',
    'SCUSDT', 'SCRTUSDT', 'SFPUSDT', 'SKLUSDT', 'SNTUSDT', 'STEEMUSDT', 'GRTUSDT',
    'STRAXUSDT', 'ICXUSDT', 'IOSTUSDT', 'IOTAUSDT', 'KSMUSDT', 'LINKUSDT', 'LITUSDT',
    'LSKUSDT', 'LTCUSDT', 'LTOUSDT', 'MANAUSDT', 'MDTUSDT', 'COCOSUSDT', 'NANOUSDT',
    'COSUSDT', 'COTIUSDT', 'CTSIUSDT', 'CVCUSDT', 'DASHUSDT', 'DCRUSDT', 'DENTUSDT',
    'DGBUSDT', 'DOCKUSDT', 'DOGEUSDT', 'ICPUSDT', 'DOTUSDT', 'EGLDUSDT', 'ELFUSDT',
    'FTMUSDT', 'ENJUSDT', 'EOSUSDT', 'FIROUSDT', 'FLMUSDT', 'FETUSDT'
]

# ذاكرة لتتبع الإشارات
sent_signals_file = "data.json"

# تحميل البيانات من الملفات
def load_data(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات إلى الملفات
def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

sent_signals = load_data(sent_signals_file)

# إرسال الرسائل إلى التيلجرام
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Error: {response.json()}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
    time.sleep(1)

# جلب بيانات الشموع من Binance
def fetch_candles(symbol, timeframe="15m", limit=5):
    try:
        url = f"{BASE_URL}/api/v3/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
        response = requests.get(url, params=params, headers={"X-MBX-APIKEY": BINANCE_API_KEY})
        response.raise_for_status()
        data = response.json()
        return [{"timestamp": candle[0], "high": float(candle[2]), "close": float(candle[4])} for candle in data]
    except Exception as e:
        print(f"Error fetching candles for {symbol}: {e}")
        return []

# تنفيذ أوامر البيع والشراء
def place_order(symbol, quantity, side="BUY"):
    url = f"{BASE_URL}/api/v3/order"
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    try:
        response = requests.post(url, params=params, headers=headers)
        response.raise_for_status()
        print(f"Order {side} placed successfully for {symbol}")
        return response.json()
    except Exception as e:
        print(f"Error placing {side} order: {e}")
        return None

# إعداد الأهداف ووقف الخسارة
def prepare_targets(entry_price):
    targets = [
        round(entry_price * 1.007, 6),  # الهدف الأول: +0.7%
        round(entry_price * 1.015, 6),  # الهدف الثاني: +1.5%
        round(entry_price * 1.02, 6)    # الهدف الثالث: +2%
    ]
    stop_loss = round(entry_price * 0.95, 6)  # وقف الخسارة: -5%
    return targets, stop_loss

# التحقق من تحقيق الهدف الأول والبيع
def check_and_sell(symbol, target_price, quantity):
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {"symbol": symbol}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        current_price = float(response.json()["price"])
        if current_price >= target_price:
            place_order(symbol, quantity, side="SELL")
            send_telegram_message(f"✅ تم تحقيق الهدف الأول وبيع {quantity} من {symbol} عند السعر: {current_price}")
            return True
    except Exception as e:
        print(f"Error checking or selling: {e}")
    return False

# الوظيفة الرئيسية
def main():
    while True:
        for symbol in SYMBOLS:
            candles = fetch_candles(symbol)
            if len(candles) < 5:
                continue

            # تحديد القمة السابقة
            previous_high = candles[-2]["high"]
            last_close = candles[-1]["close"]

            # التحقق من الكسر
            if last_close > previous_high:
                entry_price = last_close
                targets, stop_loss = prepare_targets(entry_price)

                # تنفيذ الشراء
                usd_amount = 20
                quantity = round(usd_amount / entry_price, 6)
                place_order(symbol, quantity)

                # متابعة الهدف الأول والبيع
                while not check_and_sell(symbol, targets[0], quantity):
                    time.sleep(10)  # تحقق كل 10 ثوانٍ

if __name__ == "__main__":
    main()
