"""
Cron job: Insert latest 5m candles for all symbols
Run every 5 minutes at :05 seconds
"""

from data_fetcher import DataFetcher
from db_manager import DBManager
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

fh = logging.FileHandler('logs/insert_5m.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def insert_5m_candles():
    """Insert latest 5m candle for all symbols"""
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT', 
               'DOGE/USDT', 'LINK/USDT', 'ADA/USDT']
    
    fetcher = DataFetcher()
    db = DBManager()
    
    logger.info(f"=== Starting 5m candle insertion at {datetime.utcnow()} UTC ===")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            db_symbol = fetcher.get_symbol_for_db(symbol)
            
            # Fetch last 60 candles for indicators
            df = fetcher.fetch_with_indicators(symbol, '5m', limit=60)
            last_candle = df.tail(1)
            
            # Prepare and insert
            records = fetcher.prepare_for_insert(last_candle)
            db.insert_ohlcv(db_symbol, '5m', records)
            
            logger.info(f"✓ {symbol} 5m candle inserted")
            success += 1
            
        except Exception as e:
            logger.error(f"✗ {symbol} 5m failed: {e}")
            failed += 1
    
    db.close()
    
    logger.info(f"=== 5m insertion complete: {success} success, {failed} failed ===")


if __name__ == '__main__':
    insert_5m_candles()