"""
Database manager for crypto scanner
Handles PostgreSQL operations
"""

import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Tuple
import logging
import os

# Setup logging to both file and console
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('logs/db_manager.log')
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add handlers
logger.addHandler(fh)
logger.addHandler(ch)


class DBManager:
    """Manages PostgreSQL database operations"""
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection
        
        Args:
            db_url: PostgreSQL connection string (or use DB_URL env var)
        """
        self.db_url = db_url or os.getenv('DB_URL')
        if not self.db_url:
            raise ValueError("DB_URL not provided and not found in environment")
        
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = False  # Use transactions
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def insert_ohlcv(self, symbol: str, timeframe: str, records: List[Tuple]):
        """
        Insert OHLCV data with indicators into symbol_timeframe table
        Uses ON CONFLICT DO NOTHING to avoid duplicates
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: e.g., '1w', '1d', '1h'
            records: List of tuples (timestamp, open, high, low, close, volume, rsi_8, ema_20, ema_50)
        """
        table_name = f"{symbol}_{timeframe}"
        
        try:
            cursor = self.conn.cursor()
            
            query = f"""
                INSERT INTO {table_name} 
                (timestamp, open, high, low, close, volume, rsi_8, ema_20, ema_50)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO NOTHING
            """
            
            execute_batch(cursor, query, records, page_size=100)
            self.conn.commit()
            
            logger.info(f"Inserted {len(records)} candles into {table_name}")
            cursor.close()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting into {table_name}: {e}")
            raise
    
    def insert_levels(self, symbol: str, timeframe: str, records: List[Tuple], level_type: str):
        """
        Insert high or low levels into high_levels or low_levels table
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: 'daily', 'weekly', 'monthly'
            records: List of tuples (level, timestamp)
            level_type: 'high' or 'low'
        """
        table_name = f"{level_type}_levels"
        
        try:
            cursor = self.conn.cursor()
            
            query = f"""
                INSERT INTO {table_name}
                (symbol, timeframe, level, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            
            # Add symbol and timeframe to each record
            full_records = [(symbol, timeframe, level, timestamp) for level, timestamp in records]
            
            execute_batch(cursor, query, full_records, page_size=100)
            self.conn.commit()
            
            logger.info(f"Inserted {len(records)} {level_type} levels for {symbol} {timeframe}")
            cursor.close()
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting {level_type} levels: {e}")
            raise
    
    def get_candle_count(self, symbol: str, timeframe: str) -> int:
        """
        Get number of candles in a table
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: e.g., '1w'
        
        Returns:
            Count of candles
        """
        table_name = f"{symbol}_{timeframe}"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.error(f"Error counting candles in {table_name}: {e}")
            raise
    
    def get_level_count(self, symbol: str, timeframe: str, level_type: str) -> int:
        """
        Get number of levels for a symbol/timeframe
        
        Args:
            symbol: e.g., 'btcusdt'
            timeframe: 'daily', 'weekly', 'monthly'
            level_type: 'high' or 'low'
        
        Returns:
            Count of levels
        """
        table_name = f"{level_type}_levels"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE symbol = %s AND timeframe = %s",
                (symbol, timeframe)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.error(f"Error counting {level_type} levels: {e}")
            raise


def test_btc_weekly_insert():
    """Test inserting BTC weekly data and levels"""
    from data_fetcher import DataFetcher
    
    print("\n" + "="*60)
    print("Testing BTC Weekly Database Insertion")
    print("="*60)
    
    # Fetch data
    print("\n1. Fetching BTC/USDT weekly data...")
    fetcher = DataFetcher()
    df = fetcher.fetch_with_indicators('BTC/USDT', '1w', limit=1000)
    print(f"   ✓ Fetched {len(df)} complete candles")
    
    # Prepare records
    print("\n2. Preparing data for insertion...")
    candle_records = fetcher.prepare_for_insert(df)
    print(f"   ✓ Prepared {len(candle_records)} candle records")
    
    # Extract levels (high and low from each candle)
    high_records = [(row['high'], row['timestamp']) for _, row in df.iterrows()]
    low_records = [(row['low'], row['timestamp']) for _, row in df.iterrows()]
    print(f"   ✓ Extracted {len(high_records)} high levels")
    print(f"   ✓ Extracted {len(low_records)} low levels")
    
    # Connect to database
    print("\n3. Connecting to database...")
    db = DBManager()
    print("   ✓ Connected")
    
    # Insert candles
    print("\n4. Inserting candles into btcusdt_1w...")
    db.insert_ohlcv('btcusdt', '1w', candle_records)
    candle_count = db.get_candle_count('btcusdt', '1w')
    print(f"   ✓ Table now has {candle_count} candles")
    
    # Insert high levels
    print("\n5. Inserting high levels...")
    db.insert_levels('btcusdt', 'weekly', high_records, 'high')
    high_count = db.get_level_count('btcusdt', 'weekly', 'high')
    print(f"   ✓ Table now has {high_count} high levels for BTC weekly")
    
    # Insert low levels
    print("\n6. Inserting low levels...")
    db.insert_levels('btcusdt', 'weekly', low_records, 'low')
    low_count = db.get_level_count('btcusdt', 'weekly', 'low')
    print(f"   ✓ Table now has {low_count} low levels for BTC weekly")
    
    # Close connection
    db.close()
    
    print("\n" + "="*60)
    print("✓ Database insertion complete!")
    print("="*60)


if __name__ == '__main__':
    test_btc_weekly_insert()