import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests
import os
import json
from datetime import datetime

# إعداد التيلجرام
TELEGRAM_BOT_TOKEN = '7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBm'  # توكن البوت الخاص بك
TELEGRAM_CHAT_ID = '-1001664466794'  # رقم المحادثة الخاص بك

# إعداد باينانس
BINANCE_API_KEY = 'Ofcy6zfehw2ek3EaQRZlIykTjoB8PPC1WXUBPT2dE4moKhnwpZZz1iy02RLdI1VK'  # مفتاح باينانس
BINANCE_API_SECRET = '6VPKApBMS1HIUUE9Rq7kxiHwZZ9xeQvzRJEcTIyoLhqMalGExYnnxn3VgzsXmOz0'  # سر باينانس

# تحديد مكان حفظ الإشارات المرسلة
SIGNALS_FILE = 'sent_signals.json'

# إرسال الرسائل إلى التيلجرام
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
        print(f"Sent message to Telegram: {message}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# جلب بيانات الشموع
def fetch_candles(exchange, symbol, timeframe="30m", limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching candles for {symbol}: {e}")
        return pd.DataFrame()

# حساب الكسر
def detect_downtrend_breakout(df):
    if len(df) < 3:
        return False

    # التحقق من الكسر الهابط
    last_close = df['close'].iloc[-1]
    prev_high = df['high'].iloc[-2]
    trend_line_high = max(df['high'].iloc[-3], prev_high)
    return last_close > trend_line_high

# إعداد الإشارات
def prepare_signal(symbol, timeframe, entry_price):
    if timeframe == "30m":
        targets = [entry_price * 1.007, entry_price * 1.015, entry_price * 1.02]
    elif timeframe == "15m":
        targets = [entry_price * 1.005, entry_price * 1.01, entry_price * 1.015]
    stop_loss = entry_price * 0.95

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "entry_price": entry_price,
        "targets": [round(target, 6) for target in targets],
        "stop_loss": round(stop_loss, 6)
    }

# إرسال الإشارة
def send_trade_signal(signal):
    message = f"""📊 إشارة تداول جديدة:
🔹 العملة: {signal['symbol']}
🔹 الإطار الزمني: {signal['timeframe']}
🔹 الشراء: {signal['entry_price']}
🎯 الأهداف:
  - الهدف الأول: {signal['targets'][0]}
  - الهدف الثاني: {signal['targets'][1]}
  - الهدف الثالث: {signal['targets'][2]}
🔻 وقف الخسارة: {signal['stop_loss']}
"""
    send_telegram_message(message)

# متابعة الأهداف
def monitor_targets(symbol, entry_price, targets, stop_loss, timeframe, exchange):
    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            last_price = ticker['last']
            
            # تحقق من تحقيق الأهداف
            for i, target in enumerate(targets):
                if last_price >= target:
                    send_telegram_message(f"🎯 تم تحقيق الهدف {i+1} للرمز {symbol}: {target}")
                    targets[i] = float('inf')  # تعطيل الهدف الذي تم تحقيقه

            # تحقق من وقف الخسارة
            if last_price <= stop_loss:
                send_telegram_message(f"❌ تم ضرب وقف الخسارة للرمز {symbol}: {stop_loss}")
                break

            # إنهاء المتابعة إذا تم تحقيق جميع الأهداف
            if all(target == float('inf') for target in targets):
                break

            time.sleep(10)
        except Exception as e:
            print(f"Error monitoring targets for {symbol}: {e}")
            break

# الوظيفة الرئيسية
def main():
    binance = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
    })

    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT']  # العملات
    timeframes = ['15m', '30m']

    while True:
        for symbol in symbols:
            for timeframe in timeframes:
                print(f"Checking {symbol} on {timeframe}...")

                df = fetch_candles(binance, symbol, timeframe)
                if df.empty:
                    continue

                if detect_downtrend_breakout(df):
                    entry_price = df['close'].iloc[-1]
                    signal = prepare_signal(symbol, timeframe, entry_price)
                    send_trade_signal(signal)
                    monitor_targets(
                        symbol, 
                        entry_price, 
                        signal['targets'], 
                        signal['stop_loss'], 
                        timeframe, 
                        binance
                    )
        time.sleep(60)

if __name__ == "__main__":
    main()
