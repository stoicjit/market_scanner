"""
Cron job: Insert latest weekly candles for all symbols
Also inserts levels and filters them
Run weekly on Monday at 00:00:05 UTC
"""

from data_fetcher import DataFetcher
from db_manager import DBManager
from level_filter import LevelFilter
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

fh = logging.FileHandler('logs/insert_weekly.log')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


def insert_weekly_candles():
    """Insert latest weekly candle for all symbols + levels"""
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'XRP/USDT', 
               'DOGE/USDT', 'LINK/USDT', 'ADA/USDT']
    
    fetcher = DataFetcher()
    db = DBManager()
    filter_obj = LevelFilter()
    
    logger.info(f"=== Starting weekly candle insertion at {datetime.utcnow()} UTC ===")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            db_symbol = fetcher.get_symbol_for_db(symbol)
            
            # Fetch last 60 candles for indicators
            df = fetcher.fetch_with_indicators(symbol, '1w', limit=60)
            last_candle = df.tail(1)
            
            # Insert candle
            records = fetcher.prepare_for_insert(last_candle)
            db.insert_ohlcv(db_symbol, '1w', records)
            
            # Extract levels
            timestamp = last_candle.iloc[0]['timestamp']
            high = float(last_candle.iloc[0]['high'])
            low = float(last_candle.iloc[0]['low'])
            
            # Insert high level
            db.insert_levels(db_symbol, 'weekly', [(high, timestamp)], 'high')
            
            # Insert low level
            db.insert_levels(db_symbol, 'weekly', [(low, timestamp)], 'low')
            
            # Filter levels
            filter_obj.filter_symbol_timeframe(db_symbol, 'weekly')
            
            logger.info(f"✓ {symbol} weekly candle + levels inserted and filtered")
            success += 1
            
        except Exception as e:
            logger.error(f"✗ {symbol} weekly failed: {e}")
            failed += 1
    
    db.close()
    filter_obj.close()
    
    logger.info(f"=== Weekly insertion complete: {success} success, {failed} failed ===")


if __name__ == '__main__':
    insert_weekly_candles()