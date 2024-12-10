import requests
import time
from datetime import datetime, timedelta
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

# السجل لمنع الشراء المكرر
trade_log = {}

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

# التحقق من الرصيد
def check_balance():
    url = f"{BASE_URL}/api/v3/account"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        balances = response.json().get("balances", [])
        for balance in balances:
            if balance["asset"] == "USDT":
                return float(balance["free"])
    return 0.0

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
    while True:
        current_time = datetime.now()

        # التحقق من الرصيد
        balance = check_balance()
        if balance < 10:
            print("Insufficient balance. Waiting for funds...")
            time.sleep(300)
            continue

        for symbol in SYMBOLS:
            print(f"Checking opportunities for {symbol}...")

            # التحقق من السجل
            if symbol in trade_log:
                last_trade_time, last_trade_price = trade_log[symbol]
                if current_time - last_trade_time < timedelta(hours=8):
                    print(f"Skipping {symbol} due to recent trade.")
                    continue

            # تنفيذ أمر شراء بـ10 دولار
            buy_order = create_buy_order(symbol, 10)
            if buy_order and "fills" in buy_order:
                executed_qty = float(buy_order["executedQty"])
                entry_price = float(buy_order["fills"][0]["price"])
                print(f"Buy order executed for {symbol} at {entry_price}")

                # تسجيل العملية
                trade_log[symbol] = (current_time, entry_price)

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

        time.sleep(60)

if __name__ == "__main__":
    main()
