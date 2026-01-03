"""
Cron job: Insert latest 4h candles for all symbols
Then check for fakeouts against weekly levels
Run every 4 hours at :00:05 (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
"""

from data_fetcher import DataFetcher
from db_manager import DBManager
from fakeout_detector import FakeoutDetector
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler('logs/insert_4h.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def insert_4h_candles():
    """Insert latest 4h candle for all symbols and check for fakeouts"""
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT', 
               'DOGE/USDT', 'LINK/USDT', 'ADA/USDT']
    
    fetcher = DataFetcher()
    db = DBManager()
    
    logger.info(f"=== Starting 4h candle insertion at {datetime.utcnow()} UTC ===")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            db_symbol = fetcher.get_symbol_for_db(symbol)
            
            # Fetch last 60 candles for indicators
            df = fetcher.fetch_with_indicators(symbol, '4h', limit=60)
            last_candle = df.tail(1)
            
            # Prepare and insert
            records = fetcher.prepare_for_insert(last_candle)
            db.insert_ohlcv(db_symbol, '4h', records)
            
            logger.info(f"✓ {symbol} 4h candle inserted")
            success += 1
            
        except Exception as e:
            logger.error(f"✗ {symbol} 4h failed: {e}")
            failed += 1
    
    db.close()
    
    logger.info(f"=== 4h insertion complete: {success} success, {failed} failed ===")
    
    # Check for fakeouts
    logger.info("=== Checking for fakeouts ===")
    detector = FakeoutDetector()
    detector.check_all_symbols('4h')
    detector.close()
    logger.info("=== Fakeout check complete ===")


if __name__ == '__main__':
    insert_4h_candles()