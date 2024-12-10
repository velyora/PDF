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

# إنشاء توقيع للطلب
def sign_request(data):
    query_string = "&".join([f"{key}={value}" for key, value in data.items()])
    signature = hmac.new(BINANCE_SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return signature

# إرسال رسائل التيلجرام
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# جلب معلومات الحد الأدنى والخطوة السعرية للرمز
def get_symbol_info(symbol):
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    response = requests.get(url)
    if response.status_code == 200:
        symbols_info = response.json()["symbols"]
        for s in symbols_info:
            if s["symbol"] == symbol:
                for filter_ in s["filters"]:
                    if filter_["filterType"] == "PRICE_FILTER":
                        return float(filter_["tickSize"])
    return None

# تنفيذ أمر شراء
def create_buy_order(symbol, usdt_amount):
    url = f"{BASE_URL}/api/v3/order"
    data = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": usdt_amount,
        "timestamp": int(time.time() * 1000)
    }
    data["signature"] = sign_request(data)
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.post(url, params=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error creating buy order:", response.json())
        return None

# وضع أمر بيع
def create_sell_order(symbol, quantity, target_price):
    tick_size = get_symbol_info(symbol)
    if tick_size:
        target_price = round(target_price // tick_size * tick_size, 8)  # ضبط السعر
    else:
        print(f"Failed to fetch tick size for {symbol}")
        return None
    url = f"{BASE_URL}/api/v3/order"
    data = {
        "symbol": symbol,
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": f"{quantity:.8f}",
        "price": f"{target_price:.8f}",
        "timestamp": int(time.time() * 1000)
    }
    data["signature"] = sign_request(data)
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.post(url, params=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error creating sell order:", response.json())
        return None

# الوظيفة الرئيسية
def main():
    for symbol in SYMBOLS:
        print(f"Checking opportunities for {symbol}...")

        # تنفيذ أمر شراء أولي بـ10 دولار
        buy_order = create_buy_order(symbol, 10)
        if buy_order and "fills" in buy_order:
            executed_qty = float(buy_order["executedQty"])
            entry_price = float(buy_order["fills"][0]["price"])
            print(f"Buy order executed for {symbol} at {entry_price}")

            # حساب الهدف 2% أعلى
            target_price = round(entry_price * 1.01, 6)

            # وضع أمر بيع عند الهدف
            sell_order = create_sell_order(symbol, executed_qty, target_price)
            if sell_order:
                print(f"Sell order placed for {symbol} at {target_price}")
                send_telegram_message(f"""
📊 <b>Order Summary</b>
🔘 Symbol: {symbol}
✅ Bought at: {entry_price}
🎯 Sell target: {target_price}
""")
            else:
                print(f"Failed to place sell order for {symbol}")
        else:
            print(f"Failed to execute initial buy order for {symbol}")

        time.sleep(60)  # الانتظار دقيقة قبل التحقق مرة أخرى

if __name__ == "__main__":
    main()
