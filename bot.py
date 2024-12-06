import requests
import time
from Server import keep_alive
keep_alive()
# باقي الكود الخاص بك هنا

# إعداد التيلجرام
TELEGRAM_BOT_TOKEN = '7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBmM'  # توكن التيلجرام الخاص بك
TELEGRAM_CHAT_ID = '-1001664466794'  # رقم المحادثة الخاص بك

# إعداد API Binance
BINANCE_API_KEY = 'Ofcy6zfehw2ek3EaQRZlIykTjoB8PPC1WXUBPT2dE4moKhnwpZZz1iy02RLdI1VK'  # مفتاح Binance API الخاص بك
BINANCE_API_SECRET = '6VPKApBMS1HIUUE9Rq7kxiHwZZ9xeQvzRJEcTIyoLhqMalGExYnnxn3VgzsXmOz0'  # المفتاح السري

# رابط API Binance
BASE_URL = "https://api.binance.com"

# قائمة العملات
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'SXPUSDT', 'SYSUSDT',
    'TOMOUSDT', 'TRXUSDT', 'TWTUSDT', 'VETUSDT', 'VGXUSDT', 'VITEUSDT', 'VTHOUSDT',
    'WAVESUSDT', 'XLMUSDT', 'XTZUSDT', 'ZECUSDT', 'ZILUSDT', 'ZRXUSDT',
    'NEBLUSDT', 'NEOUSDT', 'OGNUSDT', 'OMGUSDT', 'ONGUSDT', 'ONTUSDT',
    'OXTUSDT', 'RSRUSDT', 'SCUSDT', 'SCRTUSDT', 'SFPUSDT', 'SKLUSDT', 'SNTUSDT',
    'STEEMUSDT', 'GRTUSDT', 'STRAXUSDT', 'ICXUSDT', 'IOSTUSDT', 'IOTAUSDT',
    'KSMUSDT', 'LINKUSDT', 'LITUSDT', 'LSKUSDT', 'LTCUSDT', 'LTOUSDT', 'MANAUSDT',
    'MDTUSDT', 'COCOSUSDT', 'NANOUSDT', 'COSUSDT', 'COTIUSDT', 'CTSIUSDT',
    'CVCUSDT', 'DASHUSDT', 'DCRUSDT', 'DENTUSDT', 'DGBUSDT', 'DOCKUSDT', 'DOGEUSDT',
    'ICPUSDT', 'DOTUSDT', 'EGLDUSDT', 'ELFUSDT', 'FTMUSDT', 'ENJUSDT', 'EOSUSDT',
    'FIROUSDT', 'FLMUSDT', 'FETUSDT'
]

# الأطر الزمنية المستخدمة
TIMEFRAMES = ['5m', '15m', '30m', '1h']

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

# جلب بيانات الشموع من Binance
def fetch_candles(symbol, timeframe="30m", limit=100):
    try:
        url = f"{BASE_URL}/api/v3/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
        response = requests.get(url, params=params, headers={"X-MBX-APIKEY": BINANCE_API_KEY})
        response.raise_for_status()
        data = response.json()
        candles = []
        for candle in data:
            candles.append({
                "timestamp": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            })
        return candles
    except Exception as e:
        print(f"Error fetching candles for {symbol} with timeframe {timeframe}: {e}")
        return []

# إعداد الأهداف بناءً على الإطار الزمني
def prepare_signal(symbol, timeframe, entry_price):
    if timeframe == "5m":
        targets = [
            round(entry_price * 1.005, 6),  # هدف أول 0.5%
            round(entry_price * 1.007, 6)  # هدف ثاني 0.7%
        ]
        stop_loss = round(entry_price * 0.95, 6)  # وقف الخسارة 5%
    elif timeframe == "15m":
        targets = [
            round(entry_price * 1.007, 6),  # هدف أول 0.7%
            round(entry_price * 1.015, 6)  # هدف ثاني 1.5%
        ]
        stop_loss = round(entry_price * 0.95, 6)  # وقف الخسارة 5%
    elif timeframe == "30m":
        targets = [
            round(entry_price * 1.015, 6),  # هدف أول 1.5%
            round(entry_price * 1.02, 6)   # هدف ثاني 2%
        ]
        stop_loss = round(entry_price * 0.90, 6)  # وقف الخسارة 10%
    elif timeframe == "1h":
        targets = [
            round(entry_price * 1.02, 6),  # هدف أول 2%
            round(entry_price * 1.03, 6)  # هدف ثاني 3%
        ]
        stop_loss = round(entry_price * 0.90, 6)  # وقف الخسارة 10%

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "entry_price": round(entry_price, 6),
        "targets": targets,
        "stop_loss": stop_loss
    }

# إرسال الإشارة
def send_trade_signal(signal):
    message = f"""📊 إشارة تداول
🔘 العملة: {signal['symbol']}
🔘 الإطار الزمني: {signal['timeframe']}
🔘 الشراء: {signal['entry_price']}
🎯 الهدف الأول: {signal['targets'][0]} (+{(signal['targets'][0] / signal['entry_price'] - 1) * 100:.1f}%)
🎯 الهدف الثاني: {signal['targets'][1]} (+{(signal['targets'][1] / signal['entry_price'] - 1) * 100:.1f}%)
━━━━━━━━━━━━━━━━
❌ وقف الخسارة: {signal['stop_loss']}
"""
    send_telegram_message(message)

# متابعة الأهداف ووقف الخسارة
def monitor_targets(symbol, entry_price, targets, stop_loss):
    achieved = False
    while not achieved:
        try:
            url = f"{BASE_URL}/api/v3/ticker/price"
            params = {"symbol": symbol}
            response = requests.get(url, params=params)
            response.raise_for_status()
            last_price = float(response.json()['price'])

            # تحقق من تحقيق الأهداف
            for i, target in enumerate(targets):
                if last_price >= target:
                    send_telegram_message(f"🎯 تم تحقيق الهدف {i+1} للرمز {symbol}: {target}")
                    achieved = True
                    break

            # تحقق من وقف الخسارة
            if last_price <= stop_loss and not achieved:
                send_telegram_message(f"❌ تم ضرب وقف الخسارة للرمز {symbol}: {stop_loss}")
                achieved = True

            time.sleep(10)
        except Exception as e:
            print(f"Error monitoring targets for {symbol}: {e}")
            break

# الوظيفة الرئيسية
def main():
    while True:
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                candles = fetch_candles(symbol, timeframe)
                if len(candles) < 4:
                    continue
                entry_price = candles[-1]['close']
                signal = prepare_signal(symbol, timeframe, entry_price)
                send_trade_signal(signal)
                monitor_targets(
                    symbol,
                    entry_price,
                    signal['targets'],
                    signal['stop_loss']
                )
        time.sleep(60)

if __name__ == "__main__":
    main()
