"""
Telegram notification system for fakeout alerts
"""

import os
import logging
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('logs/telegram.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class TelegramNotifier:
    """Sends Telegram notifications for fakeouts"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        
        self.bot = Bot(token=self.bot_token)
        logger.info("Telegram bot initialized")
    
    async def send_message(self, message: str):
        """
        Send a message to Telegram
        
        Args:
            message: Text to send
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Message sent successfully")
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise
    
    def send_fakeout_alert(self, symbol: str, timeframe: str, fakeout_type: str, 
                          level: float, candle: dict):
        """
        Send a fakeout alert
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: e.g., '1h', '4h', '1d'
            fakeout_type: 'high' or 'low'
            level: The level that was faked out
            candle: Dict with OHLC data
        """
        # Format symbol nicely
        symbol_display = symbol.upper().replace('USDT', '/USDT')
        
        # Emoji based on type
        emoji = "🔴" if fakeout_type == "high" else "🟢"
        direction = "HIGH" if fakeout_type == "high" else "LOW"
        
        # Build message
        message = f"""
{emoji} <b>FAKEOUT DETECTED</b> {emoji}

<b>Symbol:</b> {symbol_display}
<b>Timeframe:</b> {timeframe}
<b>Type:</b> {direction} Fakeout
<b>Level:</b> ${level:,.2f}

<b>Candle Data:</b>
• High: ${candle['high']:,.2f}
• Low: ${candle['low']:,.2f}
• Close: ${candle['close']:,.2f}
• Time: {candle['timestamp']}

The price wicked {'above' if fakeout_type == 'high' else 'below'} ${level:,.2f} but closed {'below' if fakeout_type == 'high' else 'above'} it.
"""
        
        # Send async
        try:
            asyncio.run(self.send_message(message))
            logger.info(f"Fakeout alert sent for {symbol} {timeframe}")
        except Exception as e:
            logger.error(f"Failed to send fakeout alert: {e}")
    
    def send_test_message(self):
        """Send a test message to verify bot is working"""
        message = "🤖 <b>Test Message</b>\n\nYour Telegram bot is working correctly!"
        asyncio.run(self.send_message(message))


def test_telegram():
    """Test Telegram notifications"""
    print("\n" + "="*70)
    print("Testing Telegram Bot")
    print("="*70)
    
    try:
        notifier = TelegramNotifier()
        
        print("\nSending test message...")
        notifier.send_test_message()
        print("✓ Test message sent!")
        
        print("\nSending fake fakeout alert...")
        fake_candle = {
            'high': 91000.00,
            'low': 88000.00,
            'close': 90950.00,
            'timestamp': '2026-01-03 04:00:00+00'
        }
        notifier.send_fakeout_alert('btcusdt', '1h', 'high', 90961.81, fake_candle)
        print("✓ Fakeout alert sent!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    test_telegram()