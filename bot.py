import ccxt
import pandas as pd
import time
import json
import asyncio
from telegram import Bot

# Binance API Settings
BINANCE_API_KEY = "Ofcy6zfehw2ek3EaQRZlIykTjoB8PPC1WXUBPT2dE4moKhnwpZZz1iy02RLdI1VK"
BINANCE_SECRET_KEY = "6VPKApBMS1HIUUE9Rq7kxiHwZZ9xeQvzRJEcTIyoLhqMalGExYnnxn3VgzsXmOz0"

# Telegram Bot Settings
TELEGRAM_TOKEN = "7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBmM"
TELEGRAM_CHAT_ID = "-1001664466794"

# Binance Exchange Setup
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True
})

# List of Symbols
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'LTC/USDT', 'DOGE/USDT',
    'BCH/USDT', 'MATIC/USDT', 'LINK/USDT', 'AVAX/USDT', 'ATOM/USDT', 'NEAR/USDT', 'TRX/USDT', 
    'ETC/USDT', 'XLM/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT', 'SAND/USDT', 'AXS/USDT',  
    'DASH/USDT', 'IOTA/USDT', 'CHZ/USDT', 'CRV/USDT', 'SNX/USDT', 'FIL/USDT', 
    'MKR/USDT', 'LRC/USDT', 'TRB/USDT'
]

# Timeframe
TIMEFRAME = "15m"

# Percentages for Take Profit and Stop Loss
TP1_PERCENT = 0.007  # Target 1 (+0.7%)
TP2_PERCENT = 0.015  # Target 2 (+1.5%)
SL_PERCENT = 0.01    # Stop Loss (-1%)

# File to store active trades
TRADES_FILE = "active_trades.json"
LOG_FILE = "signal_log.txt"

# Telegram Bot Setup
bot = Bot(token=TELEGRAM_TOKEN)

# Function to save active trades to file
def save_trades(active_trades):
    with open(TRADES_FILE, "w") as file:
        json.dump(active_trades, file)

# Function to load active trades from file
def load_trades():
    try:
        with open(TRADES_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Function to fetch data
def fetch_data(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Function to analyze data using MACD
def analyze_data(df):
    if df is None:
        return None
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    df['entry'] = (df['macd'] > df['signal']) & (df['macd'].shift(1) <= df['signal'].shift(1))
    return df

# Function to send signal to Telegram and log it to a file
async def send_signal(message):
    try:
        # Send the message to Telegram
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        
        # Log the message in a local file
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception as e:
        print(f"Error sending message: {e}")

# Main Function
async def main():
    # Load active trades from file
    active_trades = load_trades()

    while True:
        for symbol in SYMBOLS:
            print(f"Analyzing data for: {symbol}")
            df = fetch_data(symbol)
            if df is not None:
                df = analyze_data(df)

                if df is not None and not df.empty:
                    latest_row = df.iloc[-1]
                    if latest_row['entry'] and symbol not in active_trades:
                        entry_price = latest_row['close']
                        tp1 = entry_price * (1 + TP1_PERCENT)
                        tp2 = entry_price * (1 + TP2_PERCENT)
                        sl = entry_price * (1 - SL_PERCENT)

                        active_trades[symbol] = {
                            "entry_price": entry_price,
                            "tp1": tp1,
                            "tp2": tp2,
                            "sl": sl,
                            "hit_target": False,
                            "hit_stop": False,
                        }

                        print(f"Entry signal found for {symbol} at {entry_price:.4f}")
                        message = f"""
📊 Trade Signal
🔹 Symbol: {symbol}
🔹 Timeframe: {TIMEFRAME}
🔹 Entry: {entry_price:.4f}
🎯 Target 1: {tp1:.4f} (+0.7%)
🎯 Target 2: {tp2:.4f} (+1.5%)
━━━━━━━━━━━━━━━━
🔻 Stop Loss: {sl:.4f} (-1%)
━━━━━━━━━━━━━━━━
💭 Smart trading Bot 💭
"""
                        await send_signal(message)
                        save_trades(active_trades)

            if symbol in active_trades:
                trade = active_trades[symbol]
                current_price = df.iloc[-1]['close']

                if not trade["hit_target"] and current_price >= trade["tp1"]:
                    trade["hit_target"] = True
                    print(f"Target 1 hit for {symbol} at {current_price:.4f}")
                    message = f"""
🎯 Target 1 Reached!
🔹 Symbol: {symbol}
🔹 Price: {current_price:.4f}
🔹 Time: {pd.Timestamp.now()}
"""
                    await send_signal(message)
                    save_trades(active_trades)

                if not trade["hit_target"] and current_price >= trade["tp2"]:
                    trade["hit_target"] = True
                    print(f"Target 2 hit for {symbol} at {current_price:.4f}")
                    message = f"""
🎯 Target 2 Reached!
🔹 Symbol: {symbol}
🔹 Price: {current_price:.4f}
🔹 Time: {pd.Timestamp.now()}
"""
                    await send_signal(message)
                    save_trades(active_trades)

                elif not trade["hit_stop"] and current_price <= trade["sl"]:
                    trade["hit_stop"] = True
                    print(f"Stop loss hit for {symbol} at {current_price:.4f}")
                    message = f"""
❌ Stop Loss Hit
🔹 Symbol: {symbol}
🔹 Price: {current_price:.4f}
🔹 Time: {pd.Timestamp.now()}
"""
                    await send_signal(message)
                    save_trades(active_trades)

                if trade["hit_target"] or trade["hit_stop"]:
                    del active_trades[symbol]
                    save_trades(active_trades)

        print("Waiting 15 minutes before analyzing new signals...")
        await asyncio.sleep(900)

if __name__ == "__main__":
    asyncio.run(main())
