from telegram import Bot

# Telegram Bot Settings
TELEGRAM_TOKEN = "7569416193:AAF8Nr7RWGGuhjhUkWrR-oFlDWaiYEVQBmM"
TELEGRAM_CHAT_ID = "1001664466794"

# Telegram Bot Setup
bot = Bot(token=TELEGRAM_TOKEN)

# Function to send a test message
def send_test_message():
    message = "✅ Bot is working and sending messages to Telegram!"
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

if __name__ == "__main__":
    send_test_message()
